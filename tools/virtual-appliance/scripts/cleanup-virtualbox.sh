# Cleanup Virtualbox
VBOX_VERSION=$(cat .vbox_version)
VBOX_ISO=VBoxGuestAdditions_$VBOX_VERSION.iso
rm -f $VBOX_ISO
