import { Calendar, Home, Inbox, Search, Settings, DoorOpen, LayoutDashboard, Newspaper, BookOpen, Presentation, Users, MessageCircle, MessageCircleWarning, ChartPie, CircleHelp, Phone } from "lucide-react"
import { Icon } from "@iconify/react"

import {
    Sidebar,
    SidebarContent,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
} from "@/components/ui/sidebar"

// Menu items.
const applicationTabs = [
    {
        title: "Dashboard",
        url: "/dashboard",
        icon: LayoutDashboard,
    },
    {
        title: "News",
        url: "/news",
        icon: Newspaper,
    },
    {
        title: "Policy Areas",
        url: "/policy-areas",
        icon: BookOpen,
    },
    {
        title: "Projects & Initiatives",
        url: "#",
        icon: Presentation,
    },
    {
        title: "Meetings & Events",
        url: "/meetings-events",
        icon: Users,
    },
    {
        title: "Public Feedback",
        url: "/public-feedback",
        icon: MessageCircle,
    },
]

const consultationTabs = [
    {
        title: "Report an Issue",
        url: "/report-issue",
        icon: MessageCircleWarning,
    },
    {
        title: "Open Data Portal",
        url: "/open-data-portal",
        icon: ChartPie,
    },
    {
        title: "FAQ/Help",
        url: "/faq-help",
        icon: CircleHelp,
    },
    {
        title: "Contact Us",
        url: "/contact-us",
        icon: Phone,
    },
]

export function AppSidebar() {
    return (
        <Sidebar variant="floating" collapsible="icon">

            <SidebarHeader>
                <SidebarMenu>
                    <SidebarMenuItem>
                        <SidebarMenuButton size="lg" >
                            <div className=" bg-primary py-2 px-1 rounded-md">
                                <Icon className=" text-white" icon="proicons:door-open" width="24" height="24" />
                            </div>
                            <span className=" text-lg text-primary">
                                Open<span className=" font-bold">Gov</span>
                            </span>
                        </SidebarMenuButton>
                    </SidebarMenuItem>
                </SidebarMenu>
            </SidebarHeader>

            <SidebarContent>
                <SidebarGroup>
                    <SidebarGroupLabel>Application</SidebarGroupLabel>
                    <SidebarGroupContent>
                        <SidebarMenu>
                            {applicationTabs.map((item) => (
                                <SidebarMenuItem key={item.title}>
                                    <SidebarMenuButton asChild>
                                        <a href={item.url}>
                                            <item.icon />
                                            <span>{item.title}</span>
                                        </a>
                                    </SidebarMenuButton>
                                </SidebarMenuItem>
                            ))}
                        </SidebarMenu>
                    </SidebarGroupContent>
                </SidebarGroup>

                <SidebarGroup>
                    <SidebarGroupLabel>Consultation</SidebarGroupLabel>
                    <SidebarGroupContent>
                        <SidebarMenu>
                            {consultationTabs.map((item) => (
                                <SidebarMenuItem key={item.title}>
                                    <SidebarMenuButton asChild>
                                        <a href={item.url}>
                                            <item.icon />
                                            <span>{item.title}</span>
                                        </a>
                                    </SidebarMenuButton>
                                </SidebarMenuItem>
                            ))}
                        </SidebarMenu>
                    </SidebarGroupContent>
                </SidebarGroup>
            </SidebarContent>
        </Sidebar>
    )
}
