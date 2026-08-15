from django.db import models

class Hostel(models.Model):
    class GenderType(models.TextChoices):
        BOYS = 'BOYS', 'Boys'
        GIRLS = 'GIRLS', 'Girls'
        CO_ED = 'CO_ED', 'Co-Ed'

    name = models.CharField(max_length=100, unique=True, db_index=True)
    gender_type = models.CharField(max_length=10, choices=GenderType.choices)

    def __str__(self):
        return self.name


class Block(models.Model):
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='blocks')
    name = models.CharField(max_length=50)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['hostel', 'name'], name='unique_block_per_hostel')
        ]

    def __str__(self):
        return f"{self.hostel.name} - Block {self.name}"


class Floor(models.Model):
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='floors')
    floor_number = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['block', 'floor_number'], name='unique_floor_per_block')
        ]

    def __str__(self):
        return f"{self.block} - Floor {self.floor_number}"


class Room(models.Model):
    class RoomType(models.TextChoices):
        SINGLE = 'SINGLE', 'Single'
        DOUBLE = 'DOUBLE', 'Double'
        TRIPLE = 'TRIPLE', 'Triple'

    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=20)
    room_type = models.CharField(max_length=10, choices=RoomType.choices)
    is_ac = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['floor', 'room_number'], name='unique_room_per_floor')
        ]

    def __str__(self):
        return f"Room {self.room_number} ({self.floor})"


class Bed(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='beds')
    bed_number = models.CharField(max_length=10)
    
    # is_occupied is intentionally excluded as requested, occupancy is derived from BedAllocation

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['room', 'bed_number'], name='unique_bed_per_room')
        ]

    def __str__(self):
        return f"{self.room} - Bed {self.bed_number}"
