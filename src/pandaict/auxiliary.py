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
from pandaict.utils.utils import uuid2elt
from pandaict.pilogger import pilogger

def __preserve_dtypes(df, dtypes):
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


def __get_free_id(df):
    return np.int64(0) if len(df) == 0 else df.index.values.max() + 1


class ADict(dict, MutableMapping):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # to prevent overwrite of internal attributes by new keys
        # see __valid_name()
        self.__setattr('_allow_invalid_attributes', False)

    def __build(self, obj, **kwargs):
        return obj

    # --- taken from AttrDict

    def __getstate__(self):
        return self.copy(), self._allow_invalid_attributes

    def __dir__(self):
        return list(self.keys())

    def __setstate__(self, state):
        mapping, allow_invalid_attributes = state
        self.update(mapping)
        self.__setattr('_allow_invalid_attributes', allow_invalid_attributes)

    @classmethod
    def __constructor(cls, mapping):
        return cls(mapping)

    # --- taken from MutableAttr

    def __setattr(self, key, value):
        super(MutableMapping, self).__setattr__(key, value)

    def __setattr__(self, key, value):
        if self.__valid_name(key):
            self[key] = value
        elif getattr(self, '_allow_invalid_attributes', True):
            super(MutableMapping, self).__setattr__(key, value)
        else:
            raise TypeError(
                "'{cls}' does not allow attribute creation.".format(
                    cls=self.__class__.__name__
                )
            )

    def __delattr(self, key):
        super(MutableMapping, self).__delattr__(key)

    def __delattr__(self, key, force=False):
        if self.__valid_name(key):
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
        if key not in self:
            raise AttributeError(
                "'{cls} instance has no attribute '{name}'".format(
                    cls=self.__class__.__name__, name=key
                )
            )

        return self.__build(self[key])

    def __getattr__(self, key):
        if key not in self or not self.__valid_name(key):
            raise AttributeError(
                "'{cls}' instance has no attribute '{name}'".format(
                    cls=self.__class__.__name__, name=key
                )
            )

        return self.__build(self[key])

    def __deepcopy__(self, memo):
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
                __preserve_dtypes(result[k], v.dtypes)
            else:
                setattr(result, k, copy.deepcopy(v, memo))

        result.__setattr('_allow_invalid_attributes', self._allow_invalid_attributes)
        return result

    @classmethod
    def __valid_name(cls, key):
        return (
                isinstance(key, str) and
                not hasattr(cls, key)
        )


class pandaICTNet(ADict):    
      
    version = "0.0.1"
    
    def __init__(self, *args, **kwargs):        
        super().__init__(*args, **kwargs)
        for key in self:
            if isinstance(self[key], list):
                self[key] = pd.DataFrame(np.zeros(0, dtype=self[key]), index=pd.Index([],
                                         dtype=np.int64))
        
        
               
    def deepcopy(self):
        return copy.deepcopy(self)
    
    # @FromSerializableRegistry.from_serializable.register(class_name='pandaICTNet', module_name='pandaICTNet.pandaICTNet')    
    def pandaICTNet(self):                
        net = create_empty_network()            
        net.update(self.obj)
        return net
        
    def __repr__(self):  # pragma: no cover
        par = []
        res = []
        for et in list(self.keys()):
            if not et.startswith("_") and isinstance(self[et], pd.DataFrame) and len(self[et]) > 0:
                n_rows = self[et].shape[0]
                if 'res_' in et:
                    res.append("   - %s (%i %s)" % (et, n_rows, "element" + _plural_s(n_rows)))
                elif et == 'group':
                    n_groups = len(set(self[et].index))
                    par.append('   - %s (%i %s, %i %s)' % (
                        et, n_groups, "group" + _plural_s(n_groups), n_rows, "row" + _plural_s(n_rows)))
                else:
                    par.append("   - %s (%i %s)" % (et, n_rows, "element" + _plural_s(n_rows)))
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
        """
        Compares this network to another one
        
        :INPUT:
            **other** (pandaICTNet) - pandaict network to compare to.           
            
        :OUTPUT:
            **equals** (boolean) - True if networks are equal excluding uuids and standard types, False else.  
        
        """
        keys = list(self.keys())
        if 'name' in keys:
            keys.remove('name')
        if 'std_types' in keys: 
            keys.remove('std_types')
        for k in keys:            
            cols = list(self[k].columns)
            if 'uuid' in cols: 
                cols.remove('uuid')                        
            if not(self[k].empty) and not (self[k][cols].compare(other[k][cols]).empty):
                return False                        
        return True
    
    def get_elts_by_name_dict(self, typefilter=None):
        """
        Returns dict with network element names as keys and pandaict notation element identifiers as values 
        
        :OPTIONAL:
            **typefilter** (list of string, default None) - list of element types that are to be included in the output dict. \
                Allowed values for list items: "node","link","device","app","conn". If typefilter is not given, \
                all named element types are included. 
            
        :OUTPUT:
            **elt_dict** (dict) - Dict of network element names and their identifiers.  
        
        """
        if typefilter is None:
            typefilter = ["node","link","device","app","conn"]            
        elif isinstance(typefilter, str):
            if typefilter not in ["node","link","device","app","conn"]:
                return None
            typefilter = [typefilter]
        elif isinstance(typefilter, list):
            typefilter = [tf for tf in typefilter if tf in ["node","link","device","app","conn"]]
        else:
            return None
                
        alldict = {}        
        for tf in typefilter:
            typedict = {}     
            for i,e in self[tf].iterrows():
                if e['name'] in typedict.keys():
                    logger.warn("get_elts_by_name_dict found multiple elements named "+e['name']+", some are omitted in the dict")
                    print("get_elts_by_name_dict found multiple elements named "+e['name']+", some are omitted in the dict")
                typedict.update({e['name']: (tf, i)})
            alldict.update({tf: typedict})
            
        return alldict
        
    def get_elts_by_uuid_dict(self, typefilter=None):
        """
        Returns dict with network element names as keys and pandaict element uuids as values 
        
        :OPTIONAL:
            **typefilter** (list of string, default None) - list of element types that are to be included in the output dict. \
                Allowed values for list items: "node","link","device","app","conn". If typefilter is not given, \
                all named element types are included. 
            
        :OUTPUT:
            **elt_dict** (dict) - Dict of network element names and their uuids.  
        
        """
        if typefilter is None:
            typefilter = ["node","link","device","app","conn"]            
        elif isinstance(typefilter, str):
            if typefilter not in ["node","link","device","app","conn"]:
                return None
            typefilter = [typefilter]
        elif isinstance(typefilter, list):
            typefilter = [tf for tf in typefilter if tf in ["node","link","device","app","conn"]]
        else:
            return None
        
        alldict = {}     
        for tf in typefilter:
            typedict = {}
            for i,e in self[tf].iterrows():
                typedict.update({e['name']: e['uuid']})
            alldict.update({tf: typedict})
        return alldict
        
def _plural_s(number):
    if number > 1:
        return "s"
    else:
        return ""