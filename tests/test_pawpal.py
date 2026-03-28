"""Tests for PawPal+ core behaviors."""

from pawpal_system import CareTask, Pet, Priority


def test_mark_complete_changes_status():
    task = CareTask("t1", "Morning walk", "exercise", 30, Priority.HIGH)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Bella", species="Dog", age=4)
    assert len(pet.tasks) == 0

    task1 = CareTask("t1", "Morning walk", "exercise", 30, Priority.HIGH)
    pet.add_task(task1)
    assert len(pet.tasks) == 1

    task2 = CareTask("t2", "Brush fur", "grooming", 15, Priority.MEDIUM)
    pet.add_task(task2)
    assert len(pet.tasks) == 2
