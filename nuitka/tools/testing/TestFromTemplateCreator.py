import jinja2
import os


def makeTestFromTemplate(template_path, dest_file):
    template_name = os.path.basename(template_path)
    template_dir = os.path.dirname(template_path)
    template_loader = jinja2.FileSystemLoader(searchpath=template_dir)
    template_env = jinja2.Environment(loader=template_loader)

    template = template_env.get_template(template_name).render()
    with open(dest_file.name, "w") as file:
        file.write(template)
