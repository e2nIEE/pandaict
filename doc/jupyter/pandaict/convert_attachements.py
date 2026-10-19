'''
@author: brequardt, jringelstein

SPDX-FileCopyrightText: Copyright (c) 2024-2026 by Fraunhofer IEE, Kassel. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause
'''

import nbformat
import base64
import os


def _convert_images_in_attachments(cell, attachments, output_dir, notebook_path):
    cs = cell.source
    for attachment_name, attachment_content in attachments.items():        
        for mime, data in attachment_content.items():             
            if mime.startswith('image'):
                # Decodiere das Bild und speichere es als Datei
                img_data = base64.b64decode(data)
                img_filename = os.path.join(output_dir, attachment_name)
                with open(img_filename, 'wb') as img_file:
                    img_file.write(img_data)
                # Ersetze die Anhangsreferenz durch die Bilddatei-Referenz                                          
                cs = cs.replace(f'attachment:{attachment_name}', "images/"+attachment_name).replace("\\","/")
                print(f"Attachment {attachment_name} in {os.path.basename(notebook_path)} saved to {img_filename}")
                ref = ("images/"+attachment_name).replace("\\","/")
                print(f" Replaced in cell by reference {ref}")
    return cs

def convert_attachments_to_files(notebook_path, output_dir):
    # Lade das Notebook
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)
    
    # Erstelle das Ausgabeverzeichnis, falls es nicht existiert
    os.makedirs(output_dir, exist_ok=True)

    # Durchsuche alle Zellen im Notebook
    for cell in nb.cells:
        if cell.cell_type == 'markdown' and 'attachments' in cell:
            attachments = cell['attachments']   
            if cell['attachments']=={}: 
                cell.pop('attachments')
            else:
                cell.source = _convert_images_in_attachments(cell, attachments, output_dir, notebook_path)
                cell.pop('attachments')
                        		
    
    # Speichere das angepasste Notebook
    with open(notebook_path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)


# Pfad zum Notebook und Ausgabeverzeichnis
if os.name=='nt':
    output_dirs = ['.\\images', '.\\howto\\images']
    input_dirs = ['.\\', '.\\howto\\']
else:
    output_dirs = ['doc/jupyter/pandaict/images', 'doc/jupyter/pandaict/howto/images']
    input_dirs = ['doc/jupyter/pandaict/', 'doc/jupyter/pandaict/howto/']

for i in range(0, len(input_dirs)):
    for direntry in os.scandir(input_dirs[i]):
        fname = direntry.name 
        if fname.endswith('ipynb'):        
            #if 'reliability-Monte' in fname:
            convert_attachments_to_files(input_dirs[i]+fname, output_dirs[i])
        
