from django.db import models
from tickets.models import Ticket

class Report(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='reports')
    report_message = models.TextField()
    message_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report {self.id} for Ticket {self.ticket.id}"
