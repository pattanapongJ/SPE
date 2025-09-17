# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

"""API Log Controller"""

from odoo.http import route, request as httprequest
from odoo.http import Controller as HttpController


DEFAULT_LOG = 'File Cannot Read'


class ApiLogControllers(HttpController):

    def get_logfile(self, api_id):
        """Return API log file. If API log file is not used return odoo log
        file from config.
        """
        api = httprequest.env['easy.api'].search([('id', '=', api_id)])
        if api and api.logfile:
            return api.logfile
        else:
            return ''

    @route([
        '/api/log/<int:api_id>',
        '/api/log/<int:api_id>/<int:tail_length>',
    ], auth='user', csrf=False)
    def log(self, api_id, tail_length=-25):
        """Easy access of log from API form in Odoo backend."""
        log_file = self.get_logfile(api_id)
        if tail_length > 0:
            tail_length = tail_length * -1
        tail = DEFAULT_LOG
        try:
            with open(log_file, 'r') as logFile:
                lines = logFile.readlines()
                tail = ''.join(lines[tail_length:])
        except FileNotFoundError:
            return f"""
                <h1>Log-File: "{log_file}" Not Found.
                """
        except IsADirectoryError:
            return f"""
                <h1>Log-File: "{log_file}" Not Found.
                """
        else:
            return f"""
<html>
<style>
html, body {{
    margin: 0;
    height: 100%;
}}
.all-wrapper {{
  height: 100%;
  display:flex;
  flex-direction:column;
}}
.wrapper-control {{
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow:hidden;
}}
.controls {{
  padding: 10px;
}}
#log {{
    flex: 1;
    color: white;
    background: black;
    overflow: auto;
}}
.log-pre {{
  margin: 10px 10px;
}}
</style>
<body>
    <div class="all-wrapper">
        <div class="wrapper-control">
            <div class="controls">
                <label for="refresh">Refresh:</label>
                <input type="checkbox" class="form-check-input" id="refresh" name="refresh" checked="true"/>
                <label for="select_length">Choose Length:</label>
                <select name="length_selection" id="select_length" onchange="tailLengthSelect(this.value)">
                    <option value="10" {'selected' if abs(tail_length)==10 else ''}>10</option>
                    <option value="20" {'selected' if abs(tail_length)==20 else ''}>20</option>
                    <option value="50" {'selected' if abs(tail_length)==50 else ''}>50</option>
                    <option value="100" {'selected' if abs(tail_length)==100 else ''}>100</option>
                    <option value="200" {'selected' if abs(tail_length)==200 else ''}>200</option>
                    <option value="500" {'selected' if abs(tail_length)==500 else ''}>500</option>
                </select>
            </div>
            <div id="log">
                <pre class="log-pre"><code>{tail}</code></pre>
            </div>
        </div>
    </div>
    <script>
        function tailLengthSelect(val) {{
            location.replace("{httprequest.httprequest.url_root}api/log/{api_id}/" + val);
        }}
        function logBottom() {{
            logArea = document.getElementById('log');
            if(logArea) {{
                logArea.scrollTop = logArea.scrollHeight;
            }}
        }}
        window.setInterval(function() {{
            autoRefresh = document.getElementById('refresh');
            if(autoRefresh && autoRefresh.checked) {{
                location.reload();
            }}
        }}, 30000);
        window.onload = logBottom;
    </script>
</body>
</html>
        """
