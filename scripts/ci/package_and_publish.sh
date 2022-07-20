package_and_publish() {
 source venv/bin/activate;
 python3 setup.py sdist;

 # Upload to Gemfury
 for FILE in dist/*; do
	curl -F package=@$FILE https://$GEMFURY_PUSH_TOKEN@push.fury.io/$GEMFURY_USER/
 done
}

package_and_publish