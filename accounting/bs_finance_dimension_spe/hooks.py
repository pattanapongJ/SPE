from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        dimension_groups = env['bs.dimension.group'].search([])
        if dimension_groups:
            # Call the method to create finance dimensions
            dimension_groups.create_finance_dimensions_initial_data()


def uninstall_hook(cr, registry):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        dimension = env['bs.dimension.group']
        dimension |= env.ref('bs_finance_dimension.bs_dimension_2', raise_if_not_found=False)
        dimension |= env.ref('bs_finance_dimension_spe.bs_dimension_4', raise_if_not_found=False)
        dimension |= env.ref('bs_finance_dimension_spe.bs_dimension_5', raise_if_not_found=False)
        dimension |= env.ref('bs_finance_dimension_spe.bs_dimension_6', raise_if_not_found=False)
        dimension |= env.ref('bs_finance_dimension_spe.bs_dimension_7', raise_if_not_found=False)
        dimension |= env.ref('bs_finance_dimension_spe.bs_dimension_8', raise_if_not_found=False)
        dimension |= env.ref('bs_finance_dimension_spe.bs_dimension_9', raise_if_not_found=False)
        dimension |= env.ref('bs_finance_dimension_spe.bs_dimension_10', raise_if_not_found=False)

        dimension_datas = env['bs.finance.dimension'].search([('group_id','in',dimension.ids)])
        dimension_datas.unlink()
