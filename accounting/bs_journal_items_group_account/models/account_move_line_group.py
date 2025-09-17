from odoo import models, fields, tools, api


class AccountMoveLineGroup(models.Model):
    _name = 'account.move.line.group'
    _description = 'Grouped Account Move Lines'
    _auto = False

    # Fields
    id = fields.Integer(string='ID', readonly=True)  # Unique identifier for each row
    move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True)
    account_id = fields.Many2one('account.account', string='Account', readonly=True)
    name = fields.Char('Labels', readonly=True)  # Concatenated names
    debit = fields.Float(string='Debit', readonly=True)
    credit = fields.Float(string='Credit', readonly=True)
    group_mode = fields.Selection([
        ('group', 'Grouped'),
        ('split', 'Split'),
    ], string='Mode', readonly=True)

    @api.model
    def _select(self):
        """
        Base SELECT clause of the SQL query.
        Extend this method to add more fields in child modules.
        """
        return """
            SELECT 
                (aml.move_id::text || aml.account_id::text)::bigint AS id,
                aml.move_id AS move_id,
                aml.account_id AS account_id,
                STRING_AGG(aml.name::text, ', ') AS name,
                SUM(aml.debit) AS debit,
                SUM(aml.credit) AS credit,
                'group' AS group_mode
        """
        
    def _query_split(self):
        return """
            SELECT
                ROW_NUMBER() OVER (ORDER BY aml.move_id, aml.account_id) AS id,
                aml.move_id,
                aml.account_id,
                STRING_AGG(aml.name, ', ') AS name,
                SUM(CASE WHEN aml.debit > 0 THEN aml.debit ELSE 0 END) AS debit,
                SUM(CASE WHEN aml.credit > 0 THEN aml.credit ELSE 0 END) AS credit,
                'split' AS group_mode
            FROM account_move_line aml
            GROUP BY aml.move_id, aml.account_id, CASE WHEN aml.debit > 0 THEN 'D' ELSE 'C' END
        """

    @api.model
    def _from(self):
        """
        FROM clause of the SQL query.
        Extend this method to modify or add joins in child modules.
        """
        return """
            FROM account_move_line aml
        """

    @api.model
    def _group_by(self):
        """
        GROUP BY clause of the SQL query.
        Extend this method to modify grouping logic in child modules.
        """
        return """
            GROUP BY aml.move_id, aml.account_id
        """

    def init(self):
        """
        Initialize the view using the _select, _from, and _group_by methods.
        """
        tools.drop_view_if_exists(self._cr, self._table)
        query = f"""
            {self._select()}
            {self._from()}
            {self._group_by()}
            UNION ALL
            {self._query_split()}
        """
        self._cr.execute(f"CREATE OR REPLACE VIEW {self._table} AS ({query})")