#download ledgers 
wget --continue https://bnano.info/public/saved_ledgers/3pr_init.ldb -P app/data/ledgers/ &
wget --continue https://bnano.info/public/saved_ledgers/6pr_init.ldb -P app/data/ledgers/ &
wget --continue https://bnano.info/public/saved_ledgers/10pr_init.ldb -P app/data/ledgers/ &
wget --continue https://bnano.info/public/saved_ledgers/6pr_bucket0-1-88-90-100_10kaccs.ldb -P app/data/ledgers/ &
wget --continue https://bnano.info/public/saved_ledgers/10pr_bucket0-1-88-90-100_10kaccs.ldb -P app/data/ledgers/

#download blocks
wget --continue https://bnano.info/public/saved_blocks/3node_net.bintree.50k.json -P  app/data/blocks/ &
wget --continue https://bnano.info/public/saved_blocks/6node_bintree_100k.json -P app/data/blocks/ &
wget --continue https://bnano.info/public/saved_blocks/6node_buckets_0-1-88-90-100_10rounds.json -P app/data/blocks/ &
wget --continue https://bnano.info/public/saved_blocks/10node_100k_bintree.json -P app/data/blocks/ &
wget --continue https://bnano.info/public/saved_blocks/10node_bucket_rounds.json -P app/data/blocks/