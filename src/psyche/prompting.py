from jinja2 import Environment, PackageLoader

jinja_env = Environment(
    loader=PackageLoader("psyche", "prompts"), autoescape=False)