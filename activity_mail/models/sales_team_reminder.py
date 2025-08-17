from odoo import models, fields, api

class SalesTeamReminder(models.Model):
    _inherit = 'crm.team'

    receive_lead_upload_reminder = fields.Boolean(
        string="Receive Lead Upload Reminder",
        help="Enable this if this team should receive periodic reminders to upload leads."
    )

    @api.model
    def send_lead_upload_reminders(self):
        template = self.env.ref('activity_mail.email_template_lead_upload_reminder', raise_if_not_found=False)
        if not template:
            return
        # Only send to teams that have opted in
        teams = self.search([('receive_lead_upload_reminder', '=', True)])
        for team in teams:
            if team.member_ids:
                # Filter users with valid emails and get their formatted email addresses
                emails = [user.email_formatted for user in team.member_ids if user.email]
                email_to = ','.join(emails) if emails else False
                if email_to:
                    template.with_context(deadline_date='Friday, 5 PM').send_mail(
                        team.id,
                        force_send=True,
                        email_values={'email_to': email_to}
                    )