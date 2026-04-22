from django import forms
from .models import FichaAlumno

class FichaAlumnoForm(forms.ModelForm):
    class Meta:
        model = FichaAlumno
        exclude = ['usuario', 'fecha_registro']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_despertar': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_dormir': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'objetivo': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.DateInput, forms.TimeInput, forms.Textarea)):
                field.widget.attrs['class'] = 'form-control'