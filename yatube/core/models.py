from django.db import models

'''
Была мысль ещё и поле text добавить, но смутили различающиеся verbose_name и
help_text.
Да - можно переопределить их в форме или вообще что-то нейтральное написать,
но надо ли?..
'''


class CreatedModel(models.Model):
    """Абстрактная модель."""
    created = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )

    class Meta:
        abstract = True
