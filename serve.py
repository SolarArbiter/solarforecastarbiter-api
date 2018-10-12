import logging
from pathlib import Path

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

    def get(self):
        template = self.env.get_template(self.template)
        rendered = template.render()
        self.write(rendered)


class OrgHandler(BaseHandler):
    template = 'org/obs.html'


class DataHandler(BaseHandler):
    template = 'data/data.html'


class AccessHandler(BaseHandler):
    template = 'data/access.html'


class ReportsHandler(BaseHandler):
    template = 'data/reports.html'


class TrialsHandler(BaseHandler):
    template = 'data/trials.html'


logger=logging.getLogger()
logger.setLevel(logging.DEBUG)
static_files = Path(__file__).parent / 'static'
app = Application([(r'/', OrgHandler),
                   (r'/data', DataHandler),
                   (r'/trials', TrialsHandler),
                   (r'/access', AccessHandler),
                   (r'/reports', ReportsHandler),],
                   static_path=str(static_files),
                   autoreload=True)

app.listen('8080')
tornado.ioloop.IOLoop.current().start()


