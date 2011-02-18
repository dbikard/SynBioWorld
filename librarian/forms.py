from django import forms

class SearchForm(forms.Form):
	search= forms.CharField(max_length=100)
	cla=forms.CharField(max_length=50, 
			widget=forms.Select(choices=(('Person','Person'),
									  ('Institution','Institution'),
									  ('Paper','Paper'))))
									  
class addPapersForm(forms.Form):
	ISIdata = forms.CharField(widget=forms.Textarea)
	