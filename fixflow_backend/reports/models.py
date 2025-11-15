from django.db import models
from tickets.models import Ticket

class Report(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='reports')
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Report {self.id} for Ticket {self.ticket.id}"
    
class ReportMessage(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='messages')
    message = models.TextField()
    image = models.ImageField(upload_to='report_messages/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message {self.id} for Report {self.report.id}"
