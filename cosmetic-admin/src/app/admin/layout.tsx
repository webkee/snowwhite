import { SidebarProvider } from "@/components/admin/SidebarContext";
import { Sidebar } from "@/components/admin/Sidebar";
import { Header } from "@/components/admin/Header";
import { MobileSidebar } from "@/components/admin/MobileSidebar";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SidebarProvider>
      <Sidebar />
      <Header />
      <MobileSidebar />
      <main className="min-h-screen pt-14 md:ml-64 md:pt-14">
        <div className="p-6">{children}</div>
      </main>
    </SidebarProvider>
  );
}
