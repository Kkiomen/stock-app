import { PlaceholderPattern } from '@/components/ui/placeholder-pattern';
import AppLayout from '@/layouts/app-layout';
import { type BreadcrumbItem } from '@/types';
import { Head } from '@inertiajs/react';
import { Market, columns } from "@/components/markets/columns";
import { DataTable } from "@/components/markets/data-table";


const breadcrumbs: BreadcrumbItem[] = [
    {
        title: 'Markets',
        href: '/markets',
    },
];

export default function Markets({ stocks }: { stocks: Market[] }) {
    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title="Markets" />
            <div className="flex h-full flex-1 flex-col gap-4 rounded-xl p-4">

                <div className="border-sidebar-border/70 dark:border-sidebar-border relative min-h-[100vh] flex-1 overflow-hidden rounded-xl border md:min-h-min">
                    <DataTable columns={columns} data={stocks}/>
                </div>
            </div>
        </AppLayout>
    );
}
