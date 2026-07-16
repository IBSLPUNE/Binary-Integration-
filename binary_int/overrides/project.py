from erpnext.projects.doctype.project.project import Project
from frappe.model.naming import make_autoname
from frappe.utils import getdate


class CustomProject(Project):

    def autoname(self):
        series_name = make_autoname("PROJ-.#####")

        if self.custom_client_end_date:
            date_str = getdate(self.custom_client_end_date).strftime("%m%d%y")
            # date_str = getdate(self.custom_client_end_date).strftime("%d%m%Y")
            series_number = series_name.replace("PROJ-", "")
            self.name = f"{series_number}-{date_str}"
        else:
            self.name = series_name