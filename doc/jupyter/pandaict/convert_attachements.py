import nbformat
import base64
import os


def _convert_images_in_attachments(cell, attachments):
    for attachment_name, attachment_content in attachments.items():
        for mime, data in attachment_content.items(): 
            cs = cell.source
            if mime.startswith('image'):
                # Decodiere das Bild und speichere es als Datei
                img_data = base64.b64decode(data)
                img_filename = os.path.join(output_dir, attachment_name)
                with open(img_filename, 'wb') as img_file:
                    img_file.write(img_data)
                # Ersetze die Anhangsreferenz durch die Bilddatei-Referenz                                          
                cs = cell.source.replace(f'attachment:{attachment_name}', "images/"+attachment_name).replace("\\","/")
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
            cell.source = _convert_images_in_attachments(cell, attachments)
                        		
    
    # Speichere das angepasste Notebook
    with open(notebook_path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)


# Pfad zum Notebook und Ausgabeverzeichnis
output_dir = 'doc/jupyter/pandaict/images'
input_dir = 'doc/jupyter/pandaict/'

for direntry in os.scandir(input_dir):
    fname = direntry.name 
    if fname.endswith('ipynb'):        
        convert_attachments_to_files(input_dir+fname, output_dir)
        
