# encoding: utf-8
import io
import os
from jinja2 import Template


def render_html_report(summary):

    report_template = os.path.join(os.path.abspath(os.path.dirname(__file__)), "report_template.html")

    with io.open(report_template, "r", encoding='utf-8') as fp_r:
        template_content = fp_r.read()
        rendered_content = Template(template_content, extensions=["jinja2.ext.loopcontrols"]).render(summary)

        return rendered_content
