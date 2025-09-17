# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

"""GraphQL Doc Controllers"""

from odoo import http
from odoo.http import request


class GraphQlDocumnetations(http.Controller):
    @http.route(['/<api>/graphqldoc/data'], auth='user', csrf=False)
    def GraphQlDoc(self):
        data = request.httprequest.data.decode()
        return request.env['easyapi.graphql'].handle_query(data=data)

    @http.route(
        ['/<api>/graphqldoc/<doc_id>'],
        auth='user',
        csrf=False,
    )
    def graphQlDocController(self, api=None, **kwargs):
        return f"""
<html>
  <head>
    <title>GraphiQL</title>
    <style>
      body {{
        height: 100%;
        margin: 0;
        width: 100%;
        overflow: hidden;
      }}

      #graphiql {{
        height: 100vh;
      }}
    </style>
    <script
      src="/easy_graphql/static/lib/react/react.production.min.js"
    ></script>
    <script
      src="/easy_graphql/static/lib/react/react-dom.production.min.js"
    ></script>
    <script
      src="/easy_graphql/static/lib/graphiql/graphiql.min.js"
    ></script>
    <link rel="stylesheet" href="/easy_graphql/static/lib/graphiql/graphiql.min.css" />
    <script
      src="/easy_graphql/static/lib/graphiql/index.umd.js"
    ></script>

    <link
      rel="stylesheet"
      href="/easy_graphql/static/lib/graphiql/style.css"
    />
  </head>

  <body class="graphiql-light">
    <div id="graphiql">Loading...</div>
    <script>
      const root = ReactDOM.createRoot(document.getElementById('graphiql'));
      const fetcher = GraphiQL.createFetcher({{
        url: '/{api}/graphqldoc/data',
        headers: {{ 'X-Example-Header': 'foo' }},
      }});
      const explorerPlugin = GraphiQLPluginExplorer.explorerPlugin();
      root.render(
        React.createElement(GraphiQL, {{
          fetcher,
          defaultEditorToolsVisibility: true,
          plugins: [explorerPlugin],
        }}),
      );
      const storedTheme = localStorage.getItem('graphiql:theme');
      if (!storedTheme) {{
        localStorage.setItem('graphiql:theme', 'light');
      }}
    </script>
  </body>
</html>
        """

