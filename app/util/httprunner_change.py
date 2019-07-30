import httprunner.parser
import ast
import httprunner.client
from httprunner.utils import build_url
import time
from httprunner import logger
from requests.exceptions import (RequestException)


def parse_string_value(str_value):
    """ parse string to number if possible
    e.g. "123" => 123
         "12.2" => 12.3
         "abc" => "abc"
         "$var" => "$var"
    """
    try:
        if '-' in str_value:
            return str_value
        else:
            return ast.literal_eval(str_value)
    except ValueError:
        return str_value
    except SyntaxError:
        # e.g. $var, ${func}
        return str_value


httprunner.parser.parse_string_value = parse_string_value


def request(self, method, url, name=None, **kwargs):

    self.init_meta_data()

    # record test name
    self.meta_data["name"] = name

    # record original request info
    self.meta_data["data"][0]["request"]["method"] = method
    self.meta_data["data"][0]["request"]["url"] = url
    kwargs.setdefault("timeout", 120)
    self.meta_data["data"][0]["request"].update(kwargs)

    # prepend url with hostname unless it's already an absolute URL
    url = build_url(self.base_url, url)

    start_timestamp = time.time()
    response = self._send_request_safe_mode(method, url, **kwargs)

    # requests包get响应内容中文乱码解决
    if response.apparent_encoding:
        response.encoding = response.apparent_encoding

    response_time_ms = round((time.time() - start_timestamp) * 1000, 2)

    # get the length of the content, but if the argument stream is set to True, we take
    # the size from the content-length header, in order to not trigger fetching of the body
    if kwargs.get("stream", False):
        content_size = int(dict(response.headers).get("content-length") or 0)
    else:
        content_size = len(response.content or "")

    # record the consumed time
    self.meta_data["stat"] = {
        "response_time_ms": response_time_ms,
        "elapsed_ms": response.elapsed.microseconds / 1000.0,
        "content_size": content_size
    }
    # record request and response histories, include 30X redirection
    response_list = response.history + [response]
    self.meta_data["data"] = [
        self.get_req_resp_record(resp_obj)
        for resp_obj in response_list
    ]
    self.meta_data["data"][0]["request"].update(kwargs)
    try:
        response.raise_for_status()
    except RequestException as e:
        logger.log_error(u"{exception}".format(exception=str(e)))
    else:
        logger.log_info(
            """status_code: {}, response_time(ms): {} ms, response_length: {} bytes\n""".format(
                response.status_code,
                response_time_ms,
                content_size
            )
        )

    return response


httprunner.client.HttpSession.request = request  # END


