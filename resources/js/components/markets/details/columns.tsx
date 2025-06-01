import { ColumnDef } from "@tanstack/react-table"
import { Button } from "@/components/ui/button"
import { MoreHorizontal } from "lucide-react"

import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {Link} from "@inertiajs/react";

type Price = {
    id: number;
    close: number;
    high: number;
    low: number;
    volume: number;
    open: number;
    date: string;
    uuid: string;
    adj_close: number;
}


export const columnsPrice: ColumnDef<Price>[] = [
    {
        accessorKey: "date",
        header: "Date",
        cell: ({ row }) => {
            const market = row.original
            return  market.date.split(" ")[0];
        },
    },
    {
        accessorKey: "close",
        header: "Close",
    },
    {
        accessorKey: "adj_close",
        header: "Adj Close",
    },
    {
        accessorKey: "high",
        header: "High",
    },
    {
        accessorKey: "low",
        header: "Low",
    },
    {
        accessorKey: "volume",
        header: "Volume",
    },
]


type Forecast = {
    date: string;
    close: number;
}


export const columnsForecast: ColumnDef<Forecast>[] = [
    {
        accessorKey: "date",
        header: "Date",
        cell: ({ row }) => {
            const market = row.original
            return  market.date.split(" ")[0];
        },
    },
    {
        accessorKey: "close",
        header: "Close",
    },
]
