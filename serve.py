import logging
from pathlib import Path
import pdb

from jinja2 import Environment, FileSystemLoader, select_autoescape
import tornado.ioloop
from tornado.web import RequestHandler, Application 


class BaseHandler(RequestHandler):
    def initialize(self):
        template_dir = Path(__file__).parent / 'templates'
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape([])
        )
    def make_breadcrumb_html(self):
        path = self.request.uri
        parts = path.split('/')
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


class OrgHandler(BaseHandler):
    template = 'org/obs.html'


class SiteHandler(BaseHandler):
    template = 'data/site.html'
    subnav = {
        "/tep/avalon_2": "Data",
        }


class DataDashHandler(BaseHandler):
    subnav = { 
        "/tep/avalon_2/ac_power": "Data",
        "/tep/avalon_2/ac_power/access": "Access",
        "/tep/avalon_2/ac_power/trials": "Active Trials",
        "/tep/avalon_2/ac_power/reports": "Reports",
    }

class DataHandler(DataDashHandler):
    template = 'data/asset.html'

class AccessHandler(DataDashHandler):
    template = 'data/access.html'


class ReportsHandler(DataDashHandler):
    template = 'data/reports.html'


class TrialsHandler(DataDashHandler):
    template = 'data/trials.html'


logger=logging.getLogger()
logger.setLevel(logging.DEBUG)
static_files = Path(__file__).parent / 'static'
app = Application([(r'/tep', OrgHandler),
                   (r'/tep/avalon_2', SiteHandler),
                   (r'/tep/avalon_2/ac_power', DataHandler),
                   (r'/tep/avalon_2/ac_power/trials', TrialsHandler),
                   (r'/tep/avalon_2/ac_power/access', AccessHandler),
                   (r'/tep/avalon_2/ac_power/reports', ReportsHandler),],
                   static_path=str(static_files),
                   autoreload=True)

app.listen('8080')
tornado.ioloop.IOLoop.current().start()


