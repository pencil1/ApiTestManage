# encoding: utf-8

import io
import os
from base64 import b64encode
from collections import Iterable
from httprunner import logger
from httprunner.compat import basestring, bytes, json, numeric_types
from jinja2 import Template
from requests.structures import CaseInsensitiveDict


def stringify_body(meta_data, request_or_response):
    headers = meta_data['{}_headers'.format(request_or_response)]
    body = meta_data.get('{}_body'.format(request_or_response))

    if isinstance(body, CaseInsensitiveDict):
        body = json.dumps(dict(body), ensure_ascii=False)

    elif isinstance(body, (dict, list)):
        body = json.dumps(body, indent=2, ensure_ascii=False)

    elif isinstance(body, bytes):
        resp_content_type = headers.get("Content-Type", "")
        try:
            if "image" in resp_content_type:
                meta_data["response_data_type"] = "image"
                body = "data:{};base64,{}".format(
                    resp_content_type,
                    b64encode(body).decode('utf-8')
                )
            else:
                body = body.decode("utf-8")
        except UnicodeDecodeError:
            pass

    elif not isinstance(body, (basestring, numeric_types, Iterable)):
        # class instance, e.g. MultipartEncoder()
        body = repr(body)

    meta_data['{}_body'.format(request_or_response)] = body


def render_html_report(summary, html_report_name=None, html_report_template=None):
    """ render html report with specified report name and template
        if html_report_name is not specified, use current datetime
        if html_report_template is not specified, use default report template
    """
    if not html_report_template:
        html_report_template = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "templates",
            "default_report_template.html"
        )
        logger.log_debug("No html report template specified, use default.")
    else:
        logger.log_info("render with html report template: {}".format(html_report_template))

    logger.log_info("Start to render Html report ...")
    logger.log_debug("render data: {}".format(summary))

    report_dir_path = os.path.join(os.path.abspath('..') + r'/reports')
    start_datetime = summary["time"]["start_at"]
    if html_report_name:
        summary["html_report_name"] = html_report_name
        report_dir_path = os.path.join(report_dir_path, html_report_name)
        html_report_name += "-{}.html".format(start_datetime)
    else:
        summary["html_report_name"] = ""

    if not os.path.isdir(report_dir_path):
        os.makedirs(report_dir_path)

    for record in summary.get("records"):
        meta_data = record['meta_data']
        stringify_body(meta_data, 'request')
        stringify_body(meta_data, 'response')
    with io.open(html_report_template, "r", encoding='utf-8') as fp_r:
        template_content = fp_r.read()
        rendered_content = Template(template_content).render(summary)

    return rendered_content
