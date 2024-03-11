'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 30.01.2024

@author: jringelstein
'''

from collections.abc import MutableMapping

#import pandaict as pi
import pandas as pd
import copy
import numpy as np

from functools import singledispatch


def _preserve_dtypes(df, dtypes):
    for item, dtype in list(dtypes.items()):
        if df.dtypes.at[item] != dtype:
            if (dtype == bool or dtype == np.bool_) and np.any(df[item].isnull()):
                raise UserWarning(f"Encountered NaN value(s) in a boolean column {item}! "
                                  f"NaN are casted to True by default, which can lead to errors. "
                                  f"Replace NaN values with True or False first.")
            try:
                df[item] = df[item].astype(dtype)
            except ValueError:
                df[item] = df[item].astype(float)


def get_free_id(df):
    """
    Returns next free ID in a dataframe
    """
    return np.int64(0) if len(df) == 0 else df.index.values.max() + 1


class ADict(dict, MutableMapping):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # to prevent overwrite of internal attributes by new keys
        # see _valid_name()
        self._setattr('_allow_invalid_attributes', False)

    def _build(self, obj, **kwargs):
        """
        We only want dict like elements to be treated as recursive AttrDicts.
        """
        return obj

    # --- taken from AttrDict

    def __getstate__(self):
        return self.copy(), self._allow_invalid_attributes

    def __dir__(self):
        return list(self.keys())

    def __setstate__(self, state):
        mapping, allow_invalid_attributes = state
        self.update(mapping)
        self._setattr('_allow_invalid_attributes', allow_invalid_attributes)

    @classmethod
    def _constructor(cls, mapping):
        return cls(mapping)

    # --- taken from MutableAttr

    def _setattr(self, key, value):
        """
        Add an attribute to the object, without attempting to add it as
        a key to the mapping (i.e. internals)
        """
        super(MutableMapping, self).__setattr__(key, value)

    def __setattr__(self, key, value):
        """
        Add an attribute.

        key: The name of the attribute
        value: The attributes contents
        """
        if self._valid_name(key):
            self[key] = value
        elif getattr(self, '_allow_invalid_attributes', True):
            super(MutableMapping, self).__setattr__(key, value)
        else:
            raise TypeError(
                "'{cls}' does not allow attribute creation.".format(
                    cls=self.__class__.__name__
                )
            )

    def _delattr(self, key):
        """
        Delete an attribute from the object, without attempting to
        remove it from the mapping (i.e. internals)
        """
        super(MutableMapping, self).__delattr__(key)

    def __delattr__(self, key, force=False):
        """
        Delete an attribute.

        key: The name of the attribute
        """
        if self._valid_name(key):
            del self[key]
        elif getattr(self, '_allow_invalid_attributes', True):
            super(MutableMapping, self).__delattr__(key)
        else:
            raise TypeError(
                "'{cls}' does not allow attribute deletion.".format(
                    cls=self.__class__.__name__
                )
            )

    def __call__(self, key):
        """
        Dynamically access a key-value pair.

        key: A key associated with a value in the mapping.

        This differs from __getitem__, because it returns a new instance
        of an Attr (if the value is a Mapping object).
        """
        if key not in self:
            raise AttributeError(
                "'{cls} instance has no attribute '{name}'".format(
                    cls=self.__class__.__name__, name=key
                )
            )

        return self._build(self[key])

    def __getattr__(self, key):
        """
        Access an item as an attribute.
        """
        if key not in self or not self._valid_name(key):
            raise AttributeError(
                "'{cls}' instance has no attribute '{name}'".format(
                    cls=self.__class__.__name__, name=key
                )
            )

        return self._build(self[key])

    def __deepcopy__(self, memo):
        """
        overloads the deepcopy function of pandapower if at least one DataFrame with column
        "object" is in net

        in addition, line geodata can contain mutable objects like lists, and it is also treated
        specially

        reason: some of these objects contain a reference to net which breaks the default deepcopy
        function. Also, the DataFrame doesn't deepcopy its elements if geodata changes in the
        lists, it affects both net instances
        This fix was introduced in pandapower 2.2.1

        """
        deep_columns = {'object', 'coords', 'geometry'}
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.items():
            if isinstance(v, pd.DataFrame) and not set(v.columns).isdisjoint(deep_columns):
                if k not in result:
                    result[k] = v.__class__(index=v.index, columns=v.columns)
                for col in v.columns:
                    if col in deep_columns:
                        result[k][col] = v[col].apply(lambda x: copy.deepcopy(x, memo))
                    else:
                        result[k][col] = copy.deepcopy(v[col], memo)
                _preserve_dtypes(result[k], v.dtypes)
            else:
                setattr(result, k, copy.deepcopy(v, memo))

        result._setattr('_allow_invalid_attributes', self._allow_invalid_attributes)
        return result

    @classmethod
    def _valid_name(cls, key):
        """
        Check whether a key is a valid attribute name.

        A key may be used as an attribute if:
         * It is a string
         * The key doesn't overlap with any class attributes (for Attr,
            those would be 'get', 'items', 'keys', 'values', 'mro', and
            'register').
        """
        return (
                isinstance(key, str) and
                not hasattr(cls, key)
        )




class pandaICTNet(ADict):
    """
    Example documentation for classes in pandaICTNet
    """    
      
    version = "0.0.1"
    
    def __init__(self, *args, **kwargs):        
        """
        Initializes a new instance of pandaICTNet

        Parameters
        ----------
        :param args: Example argument
        """
        super().__init__(*args, **kwargs)
        for key in self:
            if isinstance(self[key], list):
                self[key] = pd.DataFrame(np.zeros(0, dtype=self[key]), index=pd.Index([],
                                         dtype=np.int64))
        
        
               
    def deepcopy(self):
        return copy.deepcopy(self)
    
    # @FromSerializableRegistry.from_serializable.register(class_name='pandaICTNet', module_name='pandaICTNet.pandaICTNet')    
    def pandaICTNet(self):
        if isinstance(self.obj, str):  # backwards compatibility
            from pandapower import from_json_string
            return from_json_string(self.obj)
        else:            
            net = create_empty_network()            
            net.update(self.obj)
            return net
        
    def __repr__(self):  # pragma: no cover
        """
        See Also
        --------
        count_elements
        """
        par = []
        res = []
        for et in list(self.keys()):
            if not et.startswith("_") and isinstance(self[et], pd.DataFrame) and len(self[et]) > 0:
                n_rows = self[et].shape[0]
                if 'res_' in et:
                    res.append("   - %s (%i %s)" % (et, n_rows, "element" + plural_s(n_rows)))
                elif et == 'group':
                    n_groups = len(set(self[et].index))
                    par.append('   - %s (%i %s, %i %s)' % (
                        et, n_groups, "group" + plural_s(n_groups), n_rows, "row" + plural_s(n_rows)))
                else:
                    par.append("   - %s (%i %s)" % (et, n_rows, "element" + plural_s(n_rows)))
        res_cost = [" and the following result values:",
                    "   - %s" % "res_cost"] if "res_cost" in self.keys() else []
        if not len(par) + len(res):
            return "This pandapower network is empty"
        if len(res):
            res = [" and the following results tables:"] + res
        lines = ["This pandapower network includes the following parameter tables:"] + \
            par + res + res_cost
        return "\n".join(lines)
    
    def equals_excluding_uuids_and_std_types(self, other):
        keys = list(self.keys())
        if 'name' in keys:
            keys.remove('name')
        if 'std_types' in keys: 
            keys.remove('std_types')
        for k in keys:
            cols = list(self[k].columns)
            if 'uuid' in cols: 
                cols.remove('uuid')            
            if not (self[k][cols].compare(other[k][cols]).empty):
                return False 
        return True

def plural_s(number):
    if number > 1:
        return "s"
    else:
        return ""