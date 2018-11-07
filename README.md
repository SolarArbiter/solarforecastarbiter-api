# Solar Forecast Arbiter Dashboard
Currently just a simple tornado web server to demo the dashboard layout/design and get feedback. Contains dead links and buttons to assets that have not yet been discussed. The data and figures presented should be considered as placeholders and not representative of the intended final product.

Development dashboard hosted at [https://dev-dashboard.solarforecastarbiter.org/tep](https://dev-dashboard.solarforecastarbiter.org/tep).

### Usage/ Installation

#### Local
Install requirements with `pip install -r requirements.txt`

Run the script with `python sfa_dash/serve.py`

Open [http://localhost:8080/tep](http://localhost:8080/tep) in a browser to view the dashboard.


### Template Layout

base.html

 - Basic html structure, includes navbar, footer and head. Will conditionally include sidebar if `sidebar` variable is defined.

navbar.html
	
 - Includes header for logo/site name and main navigation.

head.html

 - The <head> html element.

sidebar.html

 - Left sidebar html to be included when the sidebar variable is defined either in a template or passed into the render() function.

footer.html

 - Site footer.

dash/

 - Dash includes secondary nav content and anything else that may be section-wide. 

data/  

 - Templates extending the `dash/data.html` dashboard.

org/

 - Templates extending the `dash/org.html` dashboard.
