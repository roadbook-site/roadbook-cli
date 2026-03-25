import os
import json
import shutil
import tempfile
from pathlib import Path
from ..core.api import APIClient
from ..core.roadbook import RoadbookManager
from ..core.config import get_books_dir
from ..utils.output import print_info, print_success, print_error, print_table

def remote_list(args):
    client = APIClient()
    try:
        books = client.list_roadbooks()
        if not books:
            print_info("No remote roadbooks found.")
            return
            
        headers = ["ID", "Name", "Version", "Description"]
        rows = []
        for book in books:
            rows.append([
                book.get("id"),
                book.get("name"),
                book.get("version"),
                book.get("description", "")[:50]
            ])
        print_table(headers, rows)
    except Exception as e:
        print_error(f"Failed to list remote roadbooks: {e}")

def push(args):
    rb_id = args.id
    global_scope = getattr(args, 'global_scope', False)
    book = RoadbookManager.get_roadbook(rb_id, global_scope)
    if not book:
        scope_str = "global" if global_scope else "local"
        print_error(f"Roadbook '{rb_id}' not found in {scope_str} scope.")
        return

    client = APIClient()
    if not client.api_key:
        from ..core.config import get_server_url, set_api_key
        server_url = get_server_url()
        print_error("You are not logged in.")
        print_info(f"Please get your API key from {server_url}/settings/api-keys")
        api_key = input("Enter your API key: ").strip()
        if not api_key:
            print_error("API key is required.")
            return
        set_api_key(api_key)
        client.api_key = api_key
        client.session.headers.update({"Authorization": f"Bearer {api_key}"})

    try:
        # 1. Push Metadata
        print_info(f"Pushing metadata for '{rb_id}'...")
        data = {
            "id": book.id,
            "name": book.name,
            "version": book.version,
            "description": book.description,
            "is_public": True
        }
        client.create_roadbook(data)

        # 2. Push Content
        print_info(f"Pushing content for '{rb_id}'...")
        
        # Create temp zip
        temp_dir = tempfile.mkdtemp()
        try:
            zip_base_name = os.path.join(temp_dir, rb_id)
            # book.path is the file path (roadbook.md), parent is the directory
            source_dir = book.path.parent
            shutil.make_archive(zip_base_name, 'zip', root_dir=source_dir)
            zip_file = zip_base_name + ".zip"
            
            client.upload_content(rb_id, zip_file)
            print_success(f"Roadbook '{rb_id}' pushed successfully!")
        finally:
            shutil.rmtree(temp_dir)
            
    except Exception as e:
        print_error(f"Failed to push roadbook: {e}")

def pull(args):
    rb_id = args.id
    global_scope = getattr(args, 'global_scope', False)
    client = APIClient()
    
    try:
        # Check if exists on server
        remote_book = client.get_roadbook(rb_id)
        if not remote_book:
            print_error(f"Roadbook '{rb_id}' not found on server.")
            return

        print_info(f"Pulling roadbook '{rb_id}'...")
        
        temp_dir = tempfile.mkdtemp()
        zip_file = os.path.join(temp_dir, f"{rb_id}.zip")
        
        try:
            client.download_content(rb_id, zip_file)
            
            # Unzip to books dir
            if global_scope:
                books_dir = get_books_dir()
            else:
                books_dir = Path.cwd()
                
            target_dir = books_dir / rb_id
            
            if target_dir.exists():
                print_info(f"Overwriting existing roadbook '{rb_id}'...")
                shutil.rmtree(target_dir)
            
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.unpack_archive(zip_file, target_dir)
            print_success(f"Roadbook '{rb_id}' pulled successfully to {target_dir}")
            
        finally:
            shutil.rmtree(temp_dir)
            
    except Exception as e:
        print_error(f"Failed to pull roadbook: {e}")
