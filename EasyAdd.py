from __future__ import print_function
import oci
import os
import json
import time
from oci.config import from_file
from oci.identity.models import AddUserToGroupDetails, CreateGroupDetails, CreateUserDetails

# Configuration from specific location
config = from_file(file_location=".\\config.ini")
# Get Identity and Tenancy
identity = oci.identity.IdentityClient(config)
root_comp_id = config["tenancy"]
Tenancy = identity.get_tenancy(tenancy_id=root_comp_id).data
# Get screen size (used for divider)
screen_size = os.get_terminal_size().columns
# Create structures to hold users and groups
added_users = {}
users = {}
groups = []
groups_response = None
users_response = None

# Begin main script
def main():
    print_divider()
    print("Welcome! This script will allow you to add/remove multiple users/groups to/from your OCI tenancy." + '\n')
    start = True
    while(start):
        menu_selection = menu()
        match menu_selection:
            case 1:
                add_user()
            case 2:
                get_groups()
                add_group()
            case 3:
                get_users()
                del_user()
            case 4:
                get_groups()
                del_group()
            case 5:
                get_users()
                get_groups()
                assign_to_group()
            case 6:
                print('\n' + "Are you sure?")
                response = input("Enter Y/n: ")
                if(response.lower() == 'y'):
                    exit()
                else:
                    menu()
            case _:
                menu()

# Main menu method
def menu():
    print("Menu:")
    print('\t' + "1. Add User(s)")
    print('\t' + "2. Add Group(s)")
    print('\t' + "3. Delete User(s)")
    print('\t' + "4. Delete Group(s)")
    print('\t' + "5. Move User(s) to Existing Group")
    print('\t' + "6. Quit")
    print()
    while True:
        try:
            selection = int(input("Please Enter Choice: "))
            if selection not in range(1,7):
                print("Invalid choice. Please try again.\n")
                continue
            else:
                return selection
        except ValueError:
            print("Please enter only numbers...\n")

# Method to add user(s) to tenancy
def add_user():
    print_divider()
    while True:
        try:
            num_users = int(input("How many users to add? 0 to return: "))
            break
        except ValueError:
            print("Please enter only numbers...\n")
            continue
    if num_users > 1:
        for i in range(1,num_users + 1):
            user_name = input("Enter username: ")
            user_email = input("Enter email: ")
            user_desc = input("Description: ")
            print()
            added_users["User"+str(i)] = {
                "name": user_name,
                "email": user_email,
                "description": user_desc
            }
        request = CreateUserDetails()
        request.compartment_id = root_comp_id
        for key,value in added_users.items():
            if isinstance(value,dict):
                request.name = value.get("name")
                request.email = value.get("email")
                request.description = value.get("description")
                print("Adding "+request.name+", "+request.email+" with description: "+request.description)
                user = identity.create_user(request)
                print_divider()
    elif num_users == 1:
        user_name = input("Enter username: ")
        user_email = input("Enter email: ")
        user_desc = input("Description: ")
        print()
        request = CreateUserDetails()
        request.compartment_id = root_comp_id
        request.name = user_name
        request.email = user_email
        request.description = user_desc
        print("Adding "+request.name+", "+request.email+" with description: "+request.description)
        user = identity.create_user(request)
        print_divider()
    elif num_users == 0:
        print("Cancelled. Returning...")
        time.sleep(1.5)
        print_divider()
        return

# Method to create new groups
def add_group():
    groups_to_add = {}
    print_divider()
    print("Create a Group\n")
    print("Current groups:")
    iterator = 1
    for g in groups:
        print("\t{0}. {1}".format(iterator,g))
        iterator += 1
    print()
    while True:
        try:
            response = int(input("How many groups to create? 0 to return: "))
            break
        except ValueError:
            print("Please enter only numbers...\n")
            continue
    if response > 1:
        for i in range(0,response):
            group_name = input("Enter group name (must be unique):")
            group_desc = input("Enter a description: ")
            groups_to_add[i] = {
                "name": group_name,
                "description": group_desc
            }
    elif response == 1:
        group_name = input("Enter group name (must be unique):")
        group_desc = input("Enter a description: ")
        groups_to_add[0] = {
            "name": group_name,
            "description": group_desc
        }
    elif response == 0:
        print("Cancelled. Returning...")
        time.sleep(1.5)
        print_divider()
        return

    for k,v in groups_to_add.items():
        create_group_response = identity.create_group(
            create_group_details=oci.identity.models.CreateGroupDetails(
                compartment_id=root_comp_id,
                name=v.get("name"),
                description=v.get("description")
            )
        )
        print()
        print(create_group_response.data)
        print()
        input("Press Enter to continue...")
    time.sleep(1.5)
    print_divider()
    return

# Method to delete users from the tenancy. Current users will be listed, and then can be
# selected by list number
def del_user():
    num_users = 0
    print_divider()
    print("Delete Users"+'\n')
    print("Current users:")
    for k,v in users.items():
        num_users += 1
        for key,value in v.items():
            if key == "name":
                print('\t'+"{0}. {1}".format(num_users,value))
    while True:
        try:
            selection = int(input("Enter number of the user you wish to delete. 0 to return: "))
            break
        except ValueError:
            print("Please enter only numbers...\n")
            continue
    if selection == 0:
        print("Cancelled. Returning...")
        time.sleep(1.5)
        print_divider()
        return
    else:
        if selection > num_users:
            print("Invalid choice. Returning...")
            time.sleep(1.5)
            del_user()
        print('\n'+"Delete user with name: {0}?".format(users.get("User"+str(selection)).get("name")))
        response = input("Enter Y/n: ")
        if response.lower() == 'y':
            delete_user_response = identity.delete_user(
                user_id=users.get("User"+str(selection)).get("user_id")
            )
            print(delete_user_response.headers)
            print()
            input("Press enter to continue...")
            print_divider()
            return
        else:
            print("Cancelled. Returning...")
            time.sleep(1.5)
            del_user()

# This method deletes current groups
def del_group():
    print_divider()
    print("Delete Group\n")
    print("Current Groups:")
    num_groups = 0
    for g in groups:
        num_groups += 1
        print("\t{0}. {1}".format(num_groups,g))
    while True:
        try:
            selection = int(input("Select group to delete. It must be empty. 0 to return: "))
            break
        except ValueError:
            print("Please enter only numbers...\n")
            continue
    if selection > num_groups:
        print("Invalid choice. Returning...")
        time.sleep(1.5)
        del_group()
    elif selection == 0:
        print("Cancelled. Returning...")
        time.sleep(1.5)
        print_divider()
        return
    print("Checking that {0} group is empty...\n".format(groups[selection-1]))
    group_id = get_group_id(selection-1)

    group_membership_response = identity.list_user_group_memberships(
        compartment_id=root_comp_id,
        group_id=group_id
    )
    if not group_membership_response.data:
        print("Group {0} is empty...".format(groups[selection-1]))
        check = input("Delete it now? Y/n: ")
        if check.lower() == 'y':
            delete_group_response = identity.delete_group(
                group_id=group_id
            )
            print(delete_group_response.headers)
            input("\nPress Enter to continue...")
            del_group()
        else:
            print("Cancelled. Returning...")
            time.sleep(1.5)
            del_group()

# This method assigns users to an existing group
def assign_to_group():
    print_divider()
    print("Add User(s) to Group\n")
    print("Current Groups:")
    num_groups = 0
    for g in groups:
        num_groups += 1
        print("\t{0}. {1}".format(num_groups,g))
    while True:
        try:
            selection = int(input("\nSelect group to add to. 0 to return: "))
            break
        except ValueError:
            print("Please enter only numbers...\n")
            continue
    if selection > num_groups:
        print("Invalid selection. Please try again.")
        time.sleep(1.5)
        assign_to_group()
    elif selection == 0:
        print("Cancelled. Returning...")
        time.sleep(1.5)
        print_divider()
        return
    
    group_id = get_group_id(selection-1)
    
    print("\nCurrent Users:")
    num_users = 0
    for k,v in users.items():
        num_users += 1
        for key,value in v.items():
            if key == "name":
                print("\t{0}. {1}".format(num_users,value))
    while True:
        try:
            selection = int(input("\nSelect user to add to {0}. 0 to return: ".format(groups[selection-1])))
            break
        except ValueError:
            print("Please enter only numbers...\n")
            continue
    if selection > num_users:
        print("Invalid choice. Please try again.")
        assign_to_group()
    elif selection == 0:
        print("Cancelled. Returning...")
        time.sleep(1.5)
        print_divider()
        return
    print()
    check = input("Add {0} to group {1}? Y/n: ".format(users["User"+str(selection)].get("name"),groups[selection-1]))
    if check.lower() == 'y':
        response = identity.add_user_to_group(
            add_user_to_group_details=oci.identity.models.AddUserToGroupDetails(
                user_id=users["User"+str(selection)].get("user_id"),
                group_id=group_id
            )
        )
        print(response.data)
        input("Press enter to continue...")
        assign_to_group()
    else:
        print("Cancelled. Returning...")
        time.sleep(1.5)
        assign_to_group()

# Use get_groups() to ensure groups are up-to-date
def get_groups():
    if len(groups) == 0:
        groups_response = identity.list_groups(
            compartment_id=root_comp_id,
            sort_by="NAME",
            sort_order="ASC",
            lifecycle_state="ACTIVE"
        )
        group = json.loads(str(groups_response.data))
        for g in group:
            groups.append(g["name"])
    else:
        groups.clear()
        get_groups()

# Use get_users() to ensure users are up-to-date
def get_users():
    num_users = 0
    if len(users) == 0:
        users_response = identity.list_users(
            compartment_id=root_comp_id,
            sort_by="TIMECREATED",
            sort_order="DESC"
        )
        user = json.loads(str(users_response.data))
        for u in user:
            num_users += 1
            tags = u["defined_tags"].get("Oracle-Tags",{})
            users["User"+str(num_users)] = {
                "name": u["name"],
                "email": u["email"],
                "description": u["description"],
                "created": tags.get("CreatedOn"),
                "user_id": u["id"]
            }    
    else:
        users.clear()
        get_users()

# Method returns the OCID of the selected group name, from groups list
def get_group_id(group_number):
    if group_number is not None:
        response = identity.list_groups(
        compartment_id=root_comp_id,
        name=groups[group_number]
    )
    group = json.loads(str(response.data))
    return group[0].get("id")

# This method is only used to print a divider so lines don't run together
def print_divider():
    print('\n' + '-' * screen_size + '\n')

if __name__ == "__main__":
    main()