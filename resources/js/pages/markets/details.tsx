import { PlaceholderPattern } from '@/components/ui/placeholder-pattern';
import AppLayout from '@/layouts/app-layout';
import { type BreadcrumbItem } from '@/types';
import { Head } from '@inertiajs/react';
import {ChartContainer, ChartTooltipContent, ChartTooltip, ChartConfig} from "@/components/markets/market_chart";
import { Bar, BarChart } from "recharts"
import { Button } from "@/components/ui/button"

import {Price, columnsPrice, Forecast, columnsForecast} from "@/components/markets/details/columns";
import { DataTable } from "@/components/markets/data-table";
import { router } from "@inertiajs/react";

const breadcrumbs: BreadcrumbItem[] = [
    {
        title: 'Dashboard',
        href: '/dashboard',
    },
    {
        title: 'Markets',
        href: '/markets',
    },
    {
        title: 'Details',
        href: '#',
    },
];

type Market = {
    id: number;
    ticker: string;
    last_price_update: string;
    last_image_update: string;
    last_forecast_update: string;
    name: string;
}


const chartConfig = {
    close: {
        label: "Close",
        color: "#2563eb",
    },
} satisfies ChartConfig

const handleGenerate = (id: number) => {
    router.post(`/api/stock-analysis/run-api/clear/${id}`)
    console.log('Generate clicked for stock ID:', id);
}


export default function MarketingDetails({ stock, stockPrices, stockImage, forecast }: { stock: Market, stockPrices: Price[], stockImage: string, forecast: Forecast[] }) {

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title="Dashboard" />
            <div className="flex h-full flex-1 flex-col gap-4 rounded-xl p-4">

                <div className="">
                    <div className="grid auto-rows-min gap-4 md:grid-cols-2">
                        <div className="border-sidebar-border/70 dark:border-sidebar-border rounded-xl border text-xl font-bold p-5">
                            { stock.name } ({ stock.ticker })
                        </div>
                        <div className="border-sidebar-border/70 dark:border-sidebar-border rounded-xl border flex justify-end p-5">
                            <Button
                                onClick={() => handleGenerate(stock.id)}
                            >Generate</Button>
                        </div>
                    </div>
                </div>

                <div className="border-sidebar-border/70 dark:border-sidebar-border relative min-h-[100vh] flex-1 overflow-hidden rounded-xl border md:min-h-min">
                    <img src={stockImage} alt="Opis zdjęcia" style={{ maxWidth: '100%', height: 'auto' }} />
                </div>

                <div className="grid auto-rows-min gap-4 md:grid-cols-2">
                    <div className="border-sidebar-border/70 dark:border-sidebar-border relative aspect-video overflow-hidden rounded-xl border">
                        <DataTable columns={columnsPrice} data={stockPrices}/>
                    </div>
                    <div className="border-sidebar-border/70 dark:border-sidebar-border relative aspect-video overflow-hidden rounded-xl border">
                        <DataTable columns={columnsForecast} data={forecast}/>
                    </div>
                </div>
            </div>
        </AppLayout>
    );
}
