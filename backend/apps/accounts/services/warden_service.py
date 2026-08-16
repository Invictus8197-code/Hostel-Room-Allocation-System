from django.core.exceptions import ValidationError
from backend.apps.accounts.models import User, WardenProfile
from backend.apps.hostels.models import Hostel

class WardenServiceError(Exception):
    pass

class WardenService:
    @staticmethod
    def assign_hostels_to_warden(warden_user_id, hostel_ids):
        """
        Assigns a list of hostel IDs to a warden, strictly enforcing a maximum of 5 hostels.
        """
        try:
            user = User.objects.get(id=warden_user_id, role=User.Role.WARDEN)
        except User.DoesNotExist:
            raise WardenServiceError("User not found or is not a Warden.")

        # Strict server-side enforcement of 5-hostel limit
        if len(hostel_ids) > 5:
            raise WardenServiceError("A Warden cannot be assigned more than 5 hostels.")

        # Validate that all requested hostels exist
        hostels = Hostel.objects.filter(id__in=hostel_ids)
        if hostels.count() != len(set(hostel_ids)):
            raise WardenServiceError("One or more provided hostel IDs do not exist.")

        # Get or create WardenProfile
        profile, created = WardenProfile.objects.get_or_create(user=user)
        
        # We can safely use set() which replaces the current M2M relationship
        profile.assigned_hostels.set(hostels)
        return profile
