from django.db import models

from safedelete.models import safedelete_mixin_factory

class Auteur(safedelete_mixin_factory(policy_soft_delete=True, policy_hard_delete=True)):
    nom = models.CharField(max_length=200)

class Article(safedelete_mixin_factory(policy_soft_delete=False, policy_hard_delete=True)):
    nom = models.CharField(max_length=200)
    auteur = models.ForeignKey(Auteur) # null=True, default=None

