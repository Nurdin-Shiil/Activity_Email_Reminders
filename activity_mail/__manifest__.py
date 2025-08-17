# -*- coding: utf-8 -*-
{
    "name": "Activity Mail Reminder",
    "author": "https://github.com/codekenya",
    "summary": """
        """,
    "description": """
        Email reminders for activties.
    """,
    "version": "18.0.0.1.0",
    "depends": ['mail','base','calendar'],
    "data": ['security/ir.model.access.csv',
             'data/mail_cron.xml',
             'data/mail_template_data.xml',
             'views/activity_views.xml',
             'views/sales_team_form_view.xml'
             ],

}

