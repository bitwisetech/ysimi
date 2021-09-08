--- /fgfs/flightgear/src/FDM/YASim/yasim-test.cpp	2021-05-15 12:43:01.430057430 -0400
+++ /comm/opt/aPyt/ysimi/yasim-test.cpp	2021-09-04 16:45:43.965816390 -0400
@@ -162,6 +162,120 @@
     }
 }
 
+// duplicated command functions with ten x detail 
+
+void yasim_graph_detail(Airplane* a, const float alt, const float kts, Airplane::Configuration cfgID)
+{
+    _setup(a, cfgID, alt);
+    float speed = kts * KTS2MPS;
+    float acc[3] {0,0,0};
+    float cl_max = 0, cd_min = 1e6, ld_max = 0;
+    int   cl_max_deg = 0, cd_min_deg = 0, ld_max_deg = 0;
+    
+    printf("aoa\tlift\tdrag\n");
+    for(float  deg=-5.0; deg<=25.0 ; deg+= 0.1 ) {
+        float aoa = deg * DEG2RAD;
+        _calculateAcceleration(a, aoa, speed, acc);
+        float drag = acc[0] * (-1/9.8);
+        float lift = 1 + acc[2] * (1/9.8);
+        float ld = lift/drag;
+        
+        if (cd_min > drag) {
+            cd_min = drag;
+            cd_min_deg = deg;
+        }
+        if (cl_max < lift) {
+            cl_max = lift;
+            cl_max_deg = deg;
+        }
+        if (ld_max < ld) {
+            ld_max= ld;
+            ld_max_deg = deg;
+        }    
+        printf("%-2.1f\t%-2.3f\t%-2.3f\n", deg, lift, drag);
+    }
+    //printf("# cl_max %.4f at %d deg\n", cl_max, cl_max_deg);
+    //printf("# cd_min %.4f at %d deg\n", cd_min, cd_min_deg);
+    //printf("# ld_max %.4f at %d deg\n", ld_max, ld_max_deg);  
+}
+
+void yasim_lvsd_detail(Airplane* a, const float alt, const float kts, Airplane::Configuration cfgID)
+{
+    _setup(a, cfgID, alt);
+    float speed = kts * KTS2MPS;
+    float acc[3] {0,0,0};
+    float cl_max = 0, cd_min = 1e6, ld_max = 0;
+    int   cl_max_deg = 0, cd_min_deg = 0, ld_max_deg = 0;
+    
+    printf("aoa\tlift\tdrag\tlvsd\n");
+    for(float deg=-5; deg<=25; deg += 0.10) {
+        float aoa = deg * DEG2RAD;
+        _calculateAcceleration(a, aoa, speed, acc);
+        float drag = acc[0] * (-1/9.8);
+        float lift = 1 + acc[2] * (1/9.8);
+        float ld = lift/drag;
+        
+        if (cd_min > drag) {
+            cd_min = drag;
+            cd_min_deg = deg;
+        }
+        if (cl_max < lift) {
+            cl_max = lift;
+            cl_max_deg = deg;
+        }
+        if (ld_max < ld) {
+            ld_max= ld;
+            ld_max_deg = deg;
+        }    
+        printf("%-2.1f\t%-2.3f\t%-2.3f\t%-2.3f\n", deg, lift, drag, ld);
+    }
+    //printf("# cl_max %.4f at %d deg\n", cl_max, cl_max_deg);
+    //printf("# cd_min %.4f at %d deg\n", cd_min, cd_min_deg);
+    //printf("# ld_max %.4f at %d deg\n", ld_max, ld_max_deg);  
+}
+
+
+void yasim_drag_detail(Airplane* a, const float aoa, const float alt, Airplane::Configuration cfgID)
+{
+    _setup(a, cfgID, alt);
+    
+    float cd_min = 1e6;
+    int cd_min_kts = 0;
+    float acc[3] {0,0,0};
+    
+    printf("knots\tdrag\n");    
+    for(float kts=0; kts<=100; kts += 0.1) {
+        _calculateAcceleration(a, aoa,kts * KTS2MPS, acc);        
+        float drag = acc[0] * (-1/9.8);        
+        if (cd_min > drag) {
+            cd_min = drag;
+            cd_min_kts = kts;
+        }
+        printf("%-2.3f\t%-2.3f\n", kts, drag);
+    }
+    //printf("# cd_min %g at %d kts\n", cd_min, cd_min_kts);
+}
+
+void findMinSpeedDetail(Airplane* a, float alt)
+{
+    a->addControlSetting(Airplane::CRUISE, DEF_PROP_ELEVATOR_TRIM, 0.7f);
+    _setup(a, Airplane::CRUISE, alt);
+    float acc[3];
+
+    printf("aoa\tknots\tlift\n");
+    for(float deg=-5; deg<=25.0; deg+=0.10) {
+        float aoa = deg * DEG2RAD;
+        for(float kts = 0; kts <= 180.0; kts += 0.1) {
+            _calculateAcceleration(a, aoa, kts * KTS2MPS, acc);
+            float lift = acc[2];
+            if (lift > 0) {
+                printf("%-2.1f \t %-2.3f \t %-2.3f\n", deg, kts, ( 100 + 100 * lift));
+                break;
+            }
+        }
+    }
+}
+
 void report(Airplane* a)
 {
     printf("==========================\n");
@@ -234,8 +348,11 @@
     fprintf(stderr, "Usage: \n");
     fprintf(stderr, "  yasim <aircraft.xml> [-g [-a meters] [-s kts] [-approach | -cruise] ]\n");
     fprintf(stderr, "  yasim <aircraft.xml> [-d [-a meters] [-approach | -cruise] ]\n");
-    fprintf(stderr, "  yasim <aircraft.xml> [-m]\n");
+    fprintf(stderr, "  yasim <aircraft.xml> [-m] [-h] [--min-speed]\n");
     fprintf(stderr, "  yasim <aircraft.xml> [-test] [-a meters] [-s kts] [-approach | -cruise] ]\n");
+    fprintf(stderr, "  yasim <aircraft.xml> [--detail-graph] [--detail-drag]\n");
+    fprintf(stderr, "  yasim <aircraft.xml> [--detail-lvsd] [--detail-min-speed -approach]\n");
+    fprintf(stderr, "  yasim <aircraft.xml> [--detail-min-speed -cruise]\n");
     fprintf(stderr, "                       -g print lift/drag table: aoa, lift, drag, lift/drag \n");
     fprintf(stderr, "                       -d print drag over TAS: kts, drag\n");
     fprintf(stderr, "                       -a set altitude in meters!\n");
@@ -280,7 +397,76 @@
         Airplane::Configuration cfg = Airplane::NONE;
         float alt = 5000, kts = 100;
 
-        if((strcmp(argv[2], "-g") == 0) || test) {
+// command extensions tested first to preserve precedence
+        if((strcmp(argv[2], "--detail-graph") == 0) || test) {
+            for(int i=3; i<argc; i++) {
+                if (std::strcmp(argv[i], "-a") == 0) {
+                    if (i+1 < argc) alt = std::atof(argv[++i]);
+                }
+                else if(std::strcmp(argv[i], "-s") == 0) {
+                    if(i+1 < argc) kts = std::atof(argv[++i]);
+                }
+                else if(std::strcmp(argv[i], "-approach") == 0) cfg = Airplane::APPROACH;
+                else if(std::strcmp(argv[i], "-cruise") == 0) cfg = Airplane::CRUISE;
+                else return usage();
+            }
+            if (test) {
+                report(a);
+                printf("\n#-- lift, drag at altitude %.0f meters, %.0f knots, Config %d --\n", alt, kts, cfg);
+            }
+            yasim_graph_detail(a, alt, kts, cfg);
+            if (test) {
+                printf("\n#-- mass distribution --\n");
+                yasim_masses(a);
+            }
+        } 
+        else if((strcmp(argv[2], "--detail-lvsd") == 0) || test) {
+            for(int i=3; i<argc; i++) {
+                if (std::strcmp(argv[i], "-a") == 0) {
+                    if (i+1 < argc) alt = std::atof(argv[++i]);
+                }
+                else if(std::strcmp(argv[i], "-s") == 0) {
+                    if(i+1 < argc) kts = std::atof(argv[++i]);
+                }
+                else if(std::strcmp(argv[i], "-approach") == 0) cfg = Airplane::APPROACH;
+                else if(std::strcmp(argv[i], "-cruise") == 0) cfg = Airplane::CRUISE;
+                else return usage();
+            }
+            if (test) {
+                report(a);
+                printf("\n#-- lift, drag at altitude %.0f meters, %.0f knots, Config %d --\n", alt, kts, cfg);
+            }
+            yasim_lvsd_detail(a, alt, kts, cfg);
+            if (test) {
+                printf("\n#-- mass distribution --\n");
+                yasim_masses(a);
+            }
+        } 
+        else if(strcmp(argv[2], "--detail-drag") == 0) {
+            float alt = 2000, aoa = a->getCruiseAoA();
+            for(int i=3; i<argc; i++) {
+                if (std::strcmp(argv[i], "-a") == 0) {
+                    if (i+1 < argc) alt = std::atof(argv[++i]);
+                }
+                else if(std::strcmp(argv[i], "-approach") == 0) cfg = Airplane::APPROACH;
+                else if(std::strcmp(argv[i], "-cruise") == 0) cfg = Airplane::CRUISE;
+                else return usage();
+            }
+            yasim_drag_detail(a, aoa, alt, cfg);
+        }
+        else if(strcmp(argv[2], "--detail-min-speed") == 0) {
+            alt = 10;
+            for(int i=3; i<argc; i++) {
+                if (std::strcmp(argv[i], "-a") == 0) {
+                    if (i+1 < argc) alt = std::atof(argv[++i]);
+                }
+                else if(std::strcmp(argv[i], "-approach") == 0) cfg = Airplane::APPROACH;
+                else if(std::strcmp(argv[i], "-cruise") == 0) cfg = Airplane::CRUISE;
+                else return usage();
+            }
+            findMinSpeedDetail(a, alt);
+        }
+        else if((strcmp(argv[2], "-g") == 0) || test) {
             for(int i=3; i<argc; i++) {
                 if (std::strcmp(argv[i], "-a") == 0) {
                     if (i+1 < argc) alt = std::atof(argv[++i]);
