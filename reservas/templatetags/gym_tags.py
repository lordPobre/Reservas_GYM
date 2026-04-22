from django import template

register = template.Library()

@register.simple_tag
def get_bloque(bloques, dia, time_slot):
    # Verificamos que los datos no sean None antes de comparar
    if not bloques:
        return None
    for bloque in bloques:
        if bloque.dia == dia and bloque.inicio == time_slot:
            return bloque
    return None