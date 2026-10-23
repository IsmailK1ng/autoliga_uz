"""WebP copies (480/960/1600, quality 80) for existing product, gallery and news images (SEO task 11).

    python manage.py make_responsive_images --dry-run            # only list what would be made
    python manage.py make_responsive_images --limit 20           # first 20 originals that need copies
    python manage.py make_responsive_images --force              # remake copies even if current

Originals are never changed or deleted; copies go to MEDIA_ROOT/_resp/.
"""
from django.apps import apps
from django.core.management.base import BaseCommand

from main.images import IMAGE_FIELDS, generate, is_current, is_supported


class Command(BaseCommand):
    help = 'Create WebP copies (480/960/1600) of existing product, gallery and news images. Originals stay.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='List what would be converted, write nothing.')
        parser.add_argument('--limit', type=int, default=0, help='Convert at most N originals (0 = all).')
        parser.add_argument('--force', action='store_true', help='Remake copies that already exist.')

    def handle(self, *args, dry_run=False, limit=0, force=False, **options):
        names = []
        for label, fields in IMAGE_FIELDS.items():
            model = apps.get_model(label)
            for row in model.objects.all().values_list(*fields):
                names += [name for name in row if name]
        names = list(dict.fromkeys(names))  # the same file can be used twice
        todo = [n for n in names if is_supported(n) and (force or not is_current(n))]
        self.stdout.write(f'{len(names)} image files, {len(todo)} need copies'
                          + (f', converting the first {limit}' if limit else '') + (' (dry run)' if dry_run else ''))
        counts = {}
        for name in todo[:limit or None]:
            result = generate(name, force=force, dry_run=dry_run)
            key = result.split(':')[0]
            counts[key] = counts.get(key, 0) + 1
            self.stdout.write(f"  {'would make' if dry_run and result == 'created' else result:10} {name}")
        self.stdout.write(self.style.SUCCESS(f'done: {counts or "nothing to do"}'))
