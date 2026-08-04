db = db.getSiblingDB("admin");
db.createCollection("datasets_ops");
db.datasets_ops.insertMany([
  { name: "production_stats", docs: 1204372, last_updated: "2026-07-10T11:23:00Z" },
  { name: "cluster_config", nodes: 47, region: "us-east-1" },
  { name: "m2_sessions", count: 842, peak_rps: 42800 },
  { flag: "FLAG-6{m0ng0db_st4t1c_p4ssw0rd_l34k3d}" }
]);
