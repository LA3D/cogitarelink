#!/usr/bin/env python3

from cogitarelink.core.entity import Entity
from cogitarelink.core.processor import EntityProcessor
import uuid
import traceback

def test_credential_subject_handling():
    try:
        # Create a VC with credential subject
        vc_data = {
            "@type": "VerifiableCredential",
            "issuer": "https://example.org/issuer",
            "credentialSubject": {
                "name": "Alice",
                "@type": "Person"
            }
        }

        # Use the processor to add the VC
        ep = EntityProcessor()
        vc = ep.add(vc_data, vocab=["vc", "schema"])
        print(f"VC ID: {vc.id}")

        # Test that credential subject is stored separately but linked
        print(f"credentialSubject in VC: {vc.content.get('credentialSubject')}")
        success = True
        
        # Check that credentialSubject is a dict with @id
        if not isinstance(vc.content.get("credentialSubject"), dict):
            print("FAIL: VC should have reference to subject")
            success = False
        else:
            print("PASS: VC has reference to subject")
            
        if "@id" not in vc.content.get("credentialSubject", {}):
            print("FAIL: Subject reference should have @id")
            success = False
        else:
            print("PASS: Subject reference has @id")

        # Test that credential subject was processed correctly
        subjects = ep.get_credential_subjects(vc.id)
        print(f"Number of subjects: {len(subjects)}")
        
        if len(subjects) != 1:
            print(f"FAIL: Should have one credential subject, got {len(subjects)}")
            success = False
        else:
            print("PASS: Has one credential subject")
            
        if subjects and subjects[0].content.get("name") != "Alice":
            print(f"FAIL: Subject should have correct name, got {subjects[0].content.get('name')}")
            success = False
        elif subjects:
            print("PASS: Subject has correct name")

        # Test parent-child relationship
        children = ep.get_children(vc.id)
        print(f"Number of children: {len(children)}")
        
        if len(children) != 1:
            print(f"FAIL: VC should have one child entity, got {len(children)}")
            success = False
        else:
            print("PASS: VC has one child entity")
            
        if children and children[0].content.get("name") != "Alice":
            print(f"FAIL: Child should be the credential subject, name is {children[0].content.get('name')}")
            success = False
        elif children:
            print("PASS: Child is the credential subject with correct name")

        # Test parent lookup
        if children:
            parent = ep.get_parent(children[0].id)
            if not parent or parent.id != vc.id:
                print(f"FAIL: Parent should be the VC, got {parent.id if parent else None}")
                success = False
            else:
                print("PASS: Parent is the VC")
        
        if success:
            print("\nALL TESTS PASSED!")
        else:
            print("\nTESTS FAILED!")
            
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_credential_subject_handling()