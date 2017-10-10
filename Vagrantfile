# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "debian/stretch64"

  config.vm.synced_folder ".", "/vagrant", type: 'virtualbox'

  config.vm.network "public_network"

  config.vm.provider :virtualbox do |vb|
#    vb.customize ["modifyvm", :id, "--uart1", "0x3f8", "4"]
#    vb.customize ["modifyvm", :id, "--uartmode1", "/dev/tty.usbserial-FT94IHFD"]

#    vb.customize ["modifyvm", :id, "--usb", "on"]
#    vb.customize ["modifyvm", :id, "--usbehci", "off"]
#    vb.customize ["modifyvm", :id, "--usbxhci", "off"]

#    vb.customize ['usbfilter', 'add', '0',
#                  '--target', :id,
#                  '--name', 'FTDI TTL232R [0600]',
#                  '--vendorid', '0403',
#                  '--productid', '6001',
#                  '--revision', '0600',
#                  '--manufacturer', 'FTDI',
#                  '--product', 'TTL232R',
#                  '--serialnumber', 'FT94IHFD',
#    ]
  end
#  config.trigger.after :halt do
#    # ??? unload filter?
#  end

  config.vm.provision "shell", inline: <<-SHELL
    echo 'deb http://ppa.launchpad.net/ansible/ansible/ubuntu trusty main' >> /etc/apt/sources.list
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 93C4A3FD7BB9C367
    apt-get update
    apt-get install -y dirmngr avahi-utils zsh python-pip ckermit
    apt-get install -y --allow-unauthenticated ansible
    chsh -s /usr/bin/zsh vagrant
    usermod vagrant -a -G dialout

    pip install pyserial pexpect
  SHELL
  config.vm.provision "file", source: "~/.zshrc", destination: "$HOME/.zshrc"
  config.vm.provision "file", source: "~/.zsh", destination: "$HOME/.zsh"
#  config.vm.provision "shell", privileged: false, inline: <<-SHELL
#  SHELL
end

