import logging
from pathlib import Path
import pdb

from jinja2 import Environment, FileSystemLoader, select_autoescape
import tornado.ioloop
from tornado import httpserver
from tornado.web import RequestHandler, Application 


class BaseHandler(RequestHandler):
    def initialize(self):
        template_dir = Path(__file__).parent / 'templates'
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape([])
        )

    def path_parts(self, index=None):
        path = self.request.uri
        path = path[:path.find('?')] if '?' in path else path
        parts = path.split('/')
        if index is not None:
            return parts[index+1]
        return parts

    def format_subnav(self, **kwargs):
        formatted_subnav = {}
        for url, linktext in self.subnav_format.items():
            formatted_subnav[url.format(**kwargs)] = linktext
        return formatted_subnav
    

    def make_breadcrumb_html(self):
        parts = self.path_parts()
        breadcrumb = ""
        for idx, part in enumerate(parts):
            if part == "":
                continue
            breadcrumb += '/<a href="{}">{}</a>'.format('/'.join(parts[:idx+1]), part)
        return breadcrumb

    def get(self):
        template = self.env.get_template(self.template)
        if hasattr(self, 'subnav') and self.subnav is not None:
            subnav = self.subnav
        else:
            subnav = {}
        rendered = template.render(breadcrumb=self.make_breadcrumb_html(), current_path=self.request.uri, subnav=subnav)
        self.write(rendered)

class RootHandler(BaseHandler):
    def get(self):
        return self.redirect('/tep')


class OrgHandler(BaseHandler):
    template = 'org/obs.html'


class SiteHandler(BaseHandler):
    template = 'data/site.html'
    subnav = {
        "/tep/avalon_2": "Data",
        }


class DataDashHandler(BaseHandler):
    subnav_format = { 
        "/tep/avalon_2/{asset}": "Data",
        "/tep/avalon_2/{asset}/access": "Access",
        "/tep/avalon_2/{asset}/trials": "Active Trials",
        "/tep/avalon_2/{asset}/reports": "Reports",
    }
    def initialize(self):
        asset = self.path_parts(2)
        self.subnav = self.format_subnav(asset=asset)
        super().initialize()


class DataHandler(DataDashHandler):
    template = 'data/asset.html'


class AccessHandler(DataDashHandler):
    template = 'data/access.html'


class ReportsHandler(DataDashHandler):
    template = 'data/reports.html'


class TrialsHandler(DataDashHandler):
    template = 'data/trials.html'

class TestRegex(DataDashHandler):
    template = 'data/test.html'


logger=logging.getLogger()
logger.setLevel(logging.DEBUG)
static_files = Path(__file__).parent / 'static'
app = Application([(r'/', RootHandler),
                   (r'/tep', OrgHandler),
                   (r'/tep/avalon_2', SiteHandler),
                   (r'/tep/avalon_2/\w+', DataHandler),
                   (r'/tep/avalon_2/\w+/trials', TrialsHandler),
                   (r'/tep/avalon_2/\w+/access', AccessHandler),
                   (r'/tep/avalon_2/\w+/reports', ReportsHandler),],
                   static_path=str(static_files),
                   autoreload=True)


server = httpserver.HTTPServer(app, ssl_options={
    "certfile": "/certs/tls.crt",
    "keyfile": "/certs/tls.key",
})
server.listen(8080)
tornado.ioloop.IOLoop.current().start()
