# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import logging

_logger = logging.getLogger(__name__)

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    datetime_deadline = fields.Datetime(
        string='Due Date and Time',
        compute='_compute_datetime_deadline',
        inverse='_inverse_datetime_deadline',
        store=True
    )
    reminder_2_days_sent = fields.Boolean(
        string='2 Days Reminder Sent',
        default=False,
        help='Indicates if the 2-day reminder has been sent.'
    )
    reminder_1_day_sent = fields.Boolean(
        string='1 Day Reminder Sent',
        default=False,
        help='Indicates if the 1-day reminder has been sent.'
    )
    reminder_due_sent = fields.Boolean(
        string='Due Reminder Sent',
        default=False,
        help='Indicates if the due-today reminder has been sent.'
    )
    reminder_30_min_sent = fields.Boolean(
        string='30 Minutes Reminder Sent',
        default=False,
        help='Indicates if the 30-minute reminder has been sent.'
    )

    @api.depends('date_deadline')
    def _compute_datetime_deadline(self):
        for rec in self:
            if rec.date_deadline:
                # Set datetime_deadline to same date, at midnight
                rec.datetime_deadline = fields.Datetime.to_datetime(rec.date_deadline)
            else:
                # If no date_deadline, default to tomorrow at current hour
                now = datetime.now()
                tomorrow = now + timedelta(days=1)
                rec.datetime_deadline = tomorrow.replace(minute=0, second=0, microsecond=0)

    def _inverse_datetime_deadline(self):
        for rec in self:
            if rec.datetime_deadline:
                rec.date_deadline = rec.datetime_deadline.date()


    @api.model
    def create(self, vals):
        """Ensure date_deadline is set based on datetime_deadline during creation."""
        if 'datetime_deadline' in vals and vals['datetime_deadline']:
            vals['date_deadline'] = fields.Datetime.from_string(vals['datetime_deadline']).date()
        elif 'date_deadline' in vals and vals['date_deadline']:
            vals['datetime_deadline'] = fields.Datetime.to_datetime(vals['date_deadline'])
        elif 'date_deadline' not in vals:
            vals['date_deadline'] = fields.Date.today()
        activities = super().create(vals)
        return activities

    @api.model
    def _send_activity_reminders(self):
        """Scheduled action to send activity deadline reminders based on date_deadline."""
        today = fields.Date.today()
        activities = self.search([
            ('date_deadline', '!=', False),
            ('date_deadline', '<=', fields.Date.to_string(today + timedelta(days=2))),
            ('user_id.email', '!=', False)
        ])

        for activity in activities:
            deadline = activity.date_deadline

            days_until_deadline = (deadline - today).days

            # Select the appropriate email template and check if reminder was sent
            if days_until_deadline == 2 and not activity.reminder_2_days_sent:
                template = self.env.ref('activity_mail.mail_template_activity_reminder_2_days')
                reminder_field = 'reminder_2_days_sent'
            elif days_until_deadline == 1 and not activity.reminder_1_day_sent:
                template = self.env.ref('activity_mail.mail_template_activity_reminder_1_day')
                reminder_field = 'reminder_1_day_sent'
            elif days_until_deadline == 0 and not activity.reminder_due_sent:
                template = self.env.ref('activity_mail.mail_template_activity_reminder_due')
                reminder_field = 'reminder_due_sent'
            else:
                continue  # Skip if not applicable or reminder already sent

            # Send the email and update the reminder flag
            try:
                template.send_mail(activity.id, force_send=True)
                activity.write({reminder_field: True})
                _logger.info(f"Sent {reminder_field} for activity {activity.id}")
            except Exception as e:
                _logger.error(f"Failed to send reminder for activity {activity.id}: {str(e)}")

    @api.model
    def _send_30min_activity_reminders(self):
        """Scheduled action to send 30-minute pre-deadline reminders."""
        now = fields.Datetime.now()
        thirty_minutes_later = now + timedelta(minutes=30)
        activities = self.search([
            ('datetime_deadline', '!=', False),
            ('datetime_deadline', '>=', fields.Datetime.to_string(now)),
            ('datetime_deadline', '<=', fields.Datetime.to_string(thirty_minutes_later)),
            ('user_id.email', '!=', False),
            ('reminder_30_min_sent', '=', False)
        ])

        for activity in activities:
            template = self.env.ref('activity_mail.mail_template_activity_reminder_30_minutes')
            try:
                template.send_mail(activity.id, force_send=True)
                activity.write({'reminder_30_min_sent': True})
                _logger.info(f"Sent 30-minute reminder for activity {activity.id}")
            except Exception as e:
                _logger.error(f"Failed to send 30-minute reminder for activity {activity.id}: {str(e)}")

    def write(self, vals):
        """Reset reminder flags if deadline is changed."""
        if 'datetime_deadline' in vals or 'date_deadline' in vals:
            vals.update({
                'reminder_2_days_sent': False,
                'reminder_1_day_sent': False,
                'reminder_due_sent': False,
                'reminder_30_min_sent': False
            })
        return super().write(vals)


class MailActivitySchedule(models.TransientModel):
    _inherit = 'mail.activity.schedule'

    datetime_deadline = fields.Datetime(
        string='Due Date and Time',
        required=True,
        default=fields.Datetime.now
    )

    @api.onchange('datetime_deadline')
    def _onchange_datetime_deadline(self):
        """Update date_deadline when datetime_deadline is changed in the UI."""
        if self.datetime_deadline:
            self.date_deadline = self.datetime_deadline.date()
        else:
            self.date_deadline = fields.Date.today()

    @api.model
    def create(self, vals):
        """Ensure date_deadline and datetime_deadline are set consistently."""
        if 'datetime_deadline' in vals and vals['datetime_deadline']:
            vals['date_deadline'] = fields.Datetime.from_string(vals['datetime_deadline']).date()
        elif 'date_deadline' in vals and vals['date_deadline']:
            vals['datetime_deadline'] = fields.Datetime.to_datetime(vals['date_deadline'])
        elif 'date_deadline' not in vals:
            vals['date_deadline'] = fields.Date.today()
        activities = super().create(vals)
        return activities