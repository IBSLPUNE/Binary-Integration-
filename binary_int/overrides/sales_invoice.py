import frappe

from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from frappe.utils import getdate


class CustomSalesInvoice(SalesInvoice):

    def autoname(self):
        posting_date = getdate(self.posting_date)

        year = posting_date.year
        month = posting_date.month

        if month >= 4:
            start_year = year
            end_year = year + 1
        else:
            start_year = year - 1
            end_year = year

        fy = "FY" + str(start_year) + str(end_year)[-2:]
        short_fy = str(start_year)[-2:] + "-" + str(end_year)[-2:]

        if self.company == "Facile Info-Serv Private Limited":
            self.naming_series = ".###." + fy
            self.name = self.get_next_name("", fy, 3)

        elif self.company == "BINARY MARKETING FZCO":
            self.naming_series = ".#####."
            self.name = self.get_next_name("", "", 5)

        elif self.company == "DISCOVER INTENT FZCO":
            self.naming_series = short_fy + "/.####"
            self.name = self.get_next_name(short_fy + "/", "", 4)

        else:
            super().autoname()

    def get_next_name(self, prefix, suffix, digits):
        filters = {
            "company": self.company
        }

        if prefix and suffix:
            filters["name"] = ["like", prefix + "%" + suffix]
        elif prefix:
            filters["name"] = ["like", prefix + "%"]
        elif suffix:
            filters["name"] = ["like", "%" + suffix]

        existing_names = frappe.get_all(
            "Sales Invoice",
            filters=filters,
            pluck="name"
        )

        used_numbers = []

        for invoice_name in existing_names:
            number_part = invoice_name

            if prefix and number_part.startswith(prefix):
                number_part = number_part[len(prefix):]

            if suffix and number_part.endswith(suffix):
                number_part = number_part[:-len(suffix)]

            if number_part.isdigit():
                used_numbers.append(int(number_part))

        if used_numbers:
            next_number = max(used_numbers) + 1
        else:
            next_number = 1

        return prefix + str(next_number).zfill(digits) + suffix