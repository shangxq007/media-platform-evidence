import org.springframework.modulith.core.ApplicationModules;
public class ExposureProbe {
 public static void main(String[] args) throws Exception {
  var modules=ApplicationModules.of("com.example.platform");
  var module=modules.getModuleByName("entitlement").orElseThrow();
  var impl=Class.forName("com.example.platform.entitlement.app.EntitlementDecisionService");
  int exposed=0,query=0;
  for(var ni:module.getNamedInterfaces()) for(var type:ni) {
   if(type.getName().equals(impl.getName())) exposed++;
   if(type.getName().equals("com.example.platform.entitlement.api.EntitlementDecisionQuery")) query++;
  }
  boolean isPublic=java.lang.reflect.Modifier.isPublic(impl.getModifiers());
  System.out.println("IMPLEMENTATION_PUBLIC="+isPublic);
  System.out.println("IMPLEMENTATION_EXPOSED_COUNT="+exposed);
  System.out.println("QUERY_EXPOSED_COUNT="+query);
  if(isPublic || exposed!=0 || query!=1)throw new AssertionError("Unexpected entitlement exposure");
  System.out.println("APPLICATION_MODULES_CENSUS=PASS");
 }
}
