from compliance.models import ThirdPerson

def create_third_person(self):
    if self.finmaks_transaction.sender_account_name or self.finmaks_transaction.sender_account_name != "":
        ThirdPerson.objects.create(
            company=self.company,
            name=self.finmaks_transaction.sender_account_name,
            tc_vkn_no=self.tc_vkn_no
        )