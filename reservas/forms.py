from django import forms
from .models import FichaAlumno

class FichaAlumnoForm(forms.ModelForm):
    class Meta:
        model = FichaAlumno
        exclude = ['usuario', 'fecha_registro']
        widgets = {
            # Tus campos originales
            'fecha_nacimiento': forms.DateInput(
                format='%Y-%m-%d', 
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'hora_despertar': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_dormir': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'objetivo': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            
            # NUEVOS CAMPOS: Planes y Clínica (Con las clases correctas de Bootstrap)
            'plan': forms.Select(attrs={'class': 'form-select'}),
            'plan_nutricional': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'plan_kinesiologia': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # REFINAMIENTO MAGISTRAL: 
            # Si el widget NO tiene una clase definida arriba en el 'Meta',
            # entonces asume que es un input normal (ej. nombre, teléfono) y le pone 'form-control'.
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'