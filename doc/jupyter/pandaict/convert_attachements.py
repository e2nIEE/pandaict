import nbformat
import base64
import os

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
            for attachment_name, attachment_content in attachments.items():
                for mime, data in attachment_content.items():                    
					if mime.startswith('image'):
                        # Decodiere das Bild und speichere es als Datei
                        img_data = base64.b64decode(data)
                        img_filename = os.path.join(output_dir, attachment_name)
                        with open(img_filename, 'wb') as img_file:
                            img_file.write(img_data)
                        # Ersetze die Anhangsreferenz durch die Bilddatei-Referenz                  						
                        cell.source = cell.source.replace(f'attachment:{attachment_name}', img_filename)		
    
    # Speichere das angepasste Notebook
    with open(notebook_path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)

# Pfad zum Notebook und Ausgabeverzeichnis
notebook_path = 'pandaICT_links_and_connections.ipynb'
output_dir = 'doc/jupyter/pandaict/images'


notebook_path = 'doc/jupyter/pandaict/pandaICT_links_and_connections.ipynb'
convert_attachments_to_files(notebook_path, output_dir)
notebook_path = 'doc/jupyter/pandaict/pandaICT_reqirements_design_devgoals.ipynb'
convert_attachments_to_files(notebook_path, output_dir)
notebook_path = 'doc/jupyter/pandaict/pandaICT_scenario_useCases.ipynb'
convert_attachments_to_files(notebook_path, output_dir)
notebook_path = 'doc/jupyter/pandaict/pandaICT_tools.ipynb'
convert_attachments_to_files(notebook_path, output_dir)
notebook_path = 'doc/jupyter/pandaict/pandaICT_datamodel.ipynb'
convert_attachments_to_files(notebook_path, output_dir)
