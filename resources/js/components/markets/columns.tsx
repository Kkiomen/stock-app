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

type Market = {
    id: number;
    ticker: string;
    last_price_update: string;
    last_image_update: string;
    last_forecast_update: string;
    name: string;
}


export const columns: ColumnDef<Market>[] = [
    {
        accessorKey: "id",
        header: "ID",
        cell: ({ row }) => {
            const market = row.original

            return (
                <Link key={market.id} href={`/markets/${market.id}`}>
                    {market.id}
                </Link>
            )
        },
    },
    {
        accessorKey: "ticker",
        header: "Ticker",
        cell: ({ row }) => {
            const market = row.original

            return (
                <Link key={market.id} href={`/markets/${market.id}`}>
                    {market.ticker}
                </Link>
            )
        },
    },
    {
        accessorKey: "last_price_update",
        header: "Last Price Update",
    },
    {
        accessorKey: "last_image_update",
        header: "Last Image Update",
    },
    {
        accessorKey: "last_forecast_update",
        header: "Last Forecast Update",
    },
    {
        accessorKey: "name",
        header: "Name",
    },
    {
        header: "Actions",
        cell: ({ row }) => {
            const market = row.original

            return (
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="h-8 w-8 p-0">
                            <span className="sr-only">Open menu</span>
                            <MoreHorizontal className="h-4 w-4" />
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                        <DropdownMenuLabel>Actions</DropdownMenuLabel>
                        <DropdownMenuItem
                            onClick={() => navigator.clipboard.writeText(market.id)}
                        >
                            Copy market ID
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem>
                            <Link key={market.id} href={`/markets/${market.id}`} className="w-full">
                                View market details
                            </Link>
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            )
        },
    },
]
