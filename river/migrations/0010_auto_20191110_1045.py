# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2019-11-10 15:33
from __future__ import unicode_literals

from uuid import uuid4

import django.db.models.deletion
from django.db import migrations, models

from river.models import CANCELLED, APPROVED
from river.models.transition import DONE


def migrate_transition_meta(apps, schema_editor):
    TransitionApprovalMeta = apps.get_model('river', 'TransitionApprovalMeta')
    TransitionMeta = apps.get_model('river', 'TransitionMeta')

    for transition_approval_meta in TransitionApprovalMeta.objects.all():
        transition_meta, _ = TransitionMeta.objects.get_or_create(
            workflow=transition_approval_meta.workflow,
            source_state=transition_approval_meta.source_state,
            destination_state=transition_approval_meta.destination_state
        )

        transition_approval_meta.transition_meta = transition_meta
        transition_approval_meta.save()


def reverse_transition_meta_migration(apps, schema_editor):
    TransitionApprovalMeta = apps.get_model('river', 'TransitionApprovalMeta')
    TransitionMeta = apps.get_model('river', 'TransitionMeta')

    for transition_meta in TransitionMeta.objects.all():
        transition_meta.transition_approval_meta.all().update(source_state=transition_meta.source_state, destination_state=transition_meta.destination_state)

    TransitionApprovalMeta.objects.update(transition_meta=None)
    TransitionMeta.objects.all().delete()


def migrate_transition(apps, schema_editor):
    TransitionApproval = apps.get_model('river', 'TransitionApproval')
    Transition = apps.get_model('river', 'Transition')

    for transition_approval in TransitionApproval.objects.all():
        transition, _ = Transition.objects.get_or_create(
            workflow=transition_approval.workflow,
            source_state=transition_approval.source_state,
            destination_state=transition_approval.destination_state,
            meta=transition_approval.meta.transition_meta,
            object_id=transition_approval.object_id,
            content_type=transition_approval.content_type,
            iteration=transition_approval.iteration
        )

        transition_approval.transition = transition
        transition_approval.save()

    for transition in Transition.objects.all():
        if len(list(filter(lambda approval: approval.status == CANCELLED, transition.transition_approvals.all()))) > 0:
            transition.status = CANCELLED
            transition.save()

        elif len(list(filter(lambda approval: approval.status == APPROVED, transition.transition_approvals.all()))) == len(transition.transition_approvals.all()):
            transition.status = DONE
            transition.save()


def reverse_transition_migration(apps, schema_editor):
    TransitionApproval = apps.get_model('river', 'TransitionApproval')
    Transition = apps.get_model('river', 'Transition')

    for transition in Transition.objects.all():
        transition.transition_approvals.all().update(source_state=transition.source_state, destination_state=transition.destination_state, iteration=transition.iteration)

    TransitionApproval.objects.update(transition=None)
    Transition.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('river', '0009_auto_20191109_1806'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransitionMeta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Date Created')),
                ('date_updated', models.DateTimeField(auto_now=True, null=True, verbose_name='Date Updated')),
                ('source_state', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transition_meta_as_source', to='river.State', verbose_name='Source State')),
                (
                    'destination_state',
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transition_meta_as_destination', to='river.State', verbose_name='Destination State')),
                ('workflow', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transition_metas', to='river.Workflow', verbose_name='Workflow')),
            ],
            options={
                'verbose_name': 'Transition Meta',
                'verbose_name_plural': 'Transition Meta',
                'unique_together': set([('workflow', 'source_state', 'destination_state')]),
            },

        ),
        migrations.CreateModel(
            name='Transition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Date Created')),
                ('date_updated', models.DateTimeField(auto_now=True, null=True, verbose_name='Date Updated')),
                ('object_id', models.CharField(max_length=50, verbose_name='Related Object')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('done', 'Done')], default='pending', max_length=100, verbose_name='Status')),
                ('iteration', models.IntegerField(default=0, verbose_name='Priority')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType', verbose_name='Content Type')),
                ('workflow', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transitions', to='river.Workflow', verbose_name='Workflow')),
                ('meta', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transitions', to='river.TransitionMeta', verbose_name='Meta')),
                ('source_state', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transition_as_source', to='river.State', verbose_name='Source State')),
                ('destination_state', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transition_as_destination', to='river.State', verbose_name='Destination State')),
            ],
            options={
                'verbose_name': 'Transition',
                'verbose_name_plural': 'Transitions',
            },
        ),
        migrations.AddField(
            model_name='transitionapprovalmeta',
            name='transition_meta',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='transition_approval_meta', to='river.TransitionMeta',
                                    verbose_name='Transition Meta'),
        ),

        migrations.AlterUniqueTogether(
            name='transitionapprovalmeta',
            unique_together=set([('workflow', 'transition_meta', 'priority')]),
        ),
        migrations.RunPython(migrate_transition_meta, reverse_code=reverse_transition_meta_migration),

        migrations.AlterField(
            model_name='transitionapprovalmeta',
            name='transition_meta',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transition_approval_meta', to='river.TransitionMeta', verbose_name='Transition Meta'),
        ),

        migrations.AlterField(
            model_name='transitionapprovalmeta',
            name='destination_state',
            field=models.CharField(verbose_name='destination_state', max_length=200, default=uuid4),
            preserve_default=True,
        ),

        migrations.RemoveField(
            model_name='transitionapprovalmeta',
            name='destination_state',
        ),

        migrations.AlterField(
            model_name='transitionapprovalmeta',
            name='source_state',
            field=models.CharField(verbose_name='source_state', max_length=200, default=uuid4),
            preserve_default=True,
        ),

        migrations.RemoveField(
            model_name='transitionapprovalmeta',
            name='source_state',
        ),

        migrations.AddField(
            model_name='transitionapproval',
            name='transition',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='transition_approvals', to='river.Transition', verbose_name='Transition'),
        ),
        migrations.RunPython(migrate_transition, reverse_code=reverse_transition_migration),

        migrations.AlterField(
            model_name='transitionapproval',
            name='destination_state',
            field=models.CharField(verbose_name='destination_state', max_length=200, default=uuid4),
            preserve_default=True,
        ),

        migrations.RemoveField(
            model_name='transitionapproval',
            name='destination_state',
        ),

        migrations.AlterField(
            model_name='transitionapproval',
            name='iteration',
            field=models.CharField(verbose_name='iteration', max_length=200, default=uuid4),
            preserve_default=True,
        ),

        migrations.RemoveField(
            model_name='transitionapproval',
            name='iteration',
        ),

        migrations.AlterField(
            model_name='transitionapproval',
            name='source_state',
            field=models.CharField(verbose_name='source_state', max_length=200, default=uuid4),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='transitionapproval',
            name='source_state',
        ),
        migrations.AlterField(
            model_name='transition',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('cancelled', 'Cancelled'), ('done', 'Done')], default='pending', max_length=100, verbose_name='Status'),
        ),
        migrations.AlterField(
            model_name='transitionapproval',
            name='transition',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transition_approvals', to='river.Transition', verbose_name='Transition'),
        ),
        migrations.AlterField(
            model_name='transitionapprovalmeta',
            name='workflow',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transition_approval_metas', to='river.Workflow', verbose_name='Workflow'),
        ),
        migrations.AlterField(
            model_name='transitionmeta',
            name='workflow',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transition_metas', to='river.Workflow', verbose_name='Workflow'),
        ),
    ]
