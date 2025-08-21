///////////////////////////////////////////////////////////////////////////////////////////////////////////////
//
// AS400JConecction example.
// Purpose: This script is designed to illustrate how to use a connection to an IBM i (formerly AS/400) Server,
// using the connection and login methods with Java. Additionally it connects to a Database via SQL statements.
// Note: Where 12.34.567.89 is the Server IP address.
//
///////////////////////////////////////////////////////////////////////////////////////////////////////////////

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

public class AS400JConecction {
  public static void main(String[] args) {

     try {
        System.out.println("Trying to connect...");
        String host = System.getenv("IBMI_HOST");
        String user = System.getenv("IBMI_USER");
        String password = System.getenv("IBMI_PASS");
        String url = "jdbc:as400://" + host;
        Class.forName("com.ibm.as400.access.AS400JDBCDriver");
        try (Connection conn = DriverManager.getConnection(url, user, password);
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(
                "select employee_code, employee_name, monthly_salary from spiobjuser.nmpp960")) {
            System.out.println("Connected with " + conn);
            System.out.println("employee_code, employee_name, monthly_salary");
            while(rs.next()) {
                System.out.println(rs.getString("employee_code") + " "
                                   + rs.getString("employee_name") + " "
                                   + rs.getInt("monthly_salary"));
            }
        }
    } catch(ClassNotFoundException | SQLException e) {
       System.out.println(e.getMessage());
    }
  }
 }

